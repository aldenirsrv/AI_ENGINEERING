# indexing_pipeline.py
import hashlib
import logging
import re
import textwrap
from typing import Any, Dict, Iterable, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from settings import get_config, get_embedding_model, get_pinecone_index
from policy import policy_docs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUIRED_METADATA = [
    "policy_id",
    "status",
    "effective_date",
]


# Before indexing anything, we validate the source documents.
# In production RAG, bad metadata usually becomes bad retrieval later.
# If fields like policy_id, status, or effective_date are missing,
# the system cannot reliably filter active policies, handle versions,
# or explain where an answer came from.
def validate_policy_docs(docs: List[Dict[str, Any]]) -> None:
    """Validate required fields before indexing."""

    for idx, doc in enumerate(docs):
        if "text" not in doc or not doc["text"].strip():
            raise ValueError(f"Document {idx} is missing text.")

        if "metadata" not in doc:
            raise ValueError(f"Document {idx} is missing metadata.")

        for field in REQUIRED_METADATA:
            if field not in doc["metadata"]:
                raise ValueError(f"Document {idx} is missing metadata field: {field}")


# Naive RAG often generates random IDs for chunks.
# That works in a demo, but it creates problems in production.
# Every time the script runs, new IDs are created and the vector database
# may receive duplicated chunks.
#
# A deterministic ID makes indexing repeatable:
# same document + same section + same chunk = same vector ID.
def _normalize_text(text: str) -> str:
    """
    Normalize text to make chunk IDs stable across minor formatting changes.

    - dedent + strip
    - collapse whitespace
    - lowercase
    """
    cleaned = textwrap.dedent(text).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.lower()


def create_chunk_id(policy_id: str, section_title: str, content: str) -> str:
    """
    Create deterministic IDs to avoid duplicate vectors.

    Note: we intentionally avoid using `chunk_index` here. Chunk positions can
    drift if chunking parameters or splitter versions change, which would make
    IDs unstable across reruns even when the chunk text is identical.
    """
    raw_id = (
        f"{_normalize_text(policy_id)}:"
        f"{_normalize_text(section_title)}:"
        f"{_normalize_text(content)}"
    )
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()


# We extract the section title so every chunk carries useful context.
# This is important because a chunk may be retrieved without the full document.
# The model should still know whether the evidence came from
# "Physiotherapy Coverage", "Prior Authorization", "Exclusions", etc.
def extract_section_title(chunk: str) -> str:
    """Extract section title from text."""

    section_match = re.search(r"SECTION\s+\d+:\s*([^\n]+)", chunk, re.IGNORECASE)
    return section_match.group(1).strip() if section_match else "General Policy"


# Chunking is one of the most important decisions in a RAG system.
# If chunks are too large, retrieval becomes noisy.
# If chunks are too small, the answer may lose context.
#
# RecursiveCharacterTextSplitter tries larger separators first:
# paragraphs, then lines, then sentences, then words.
# This keeps related information together when possible.
def chunk_document(
    doc_text: str,
    metadata: Dict[str, Any],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> List[Dict[str, Any]]:
    """Split document into chunks while preserving metadata."""

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = text_splitter.split_text(doc_text)
    enhanced_chunks = []

    for chunk_index, chunk in enumerate(chunks):
        section_title = extract_section_title(chunk)

        chunk_id = create_chunk_id(
            policy_id=metadata["policy_id"],
            section_title=section_title,
            content=chunk,
        )

        # Each chunk receives both semantic content and structured metadata.
        # The content is used for semantic search.
        # The metadata is used for filtering, version control, traceability,
        # and grounded citations.
        enhanced_chunks.append(
            {
                "chunk_id": chunk_id,
                "content": chunk,
                "section_title": section_title,
                "chunk_index": chunk_index,
                **metadata,
            }
        )

    return enhanced_chunks


# Vector databases usually support batch writes.
# Batching is safer and more scalable than sending everything at once,
# especially when indexing hundreds or thousands of chunks.
def batch_items(items: List[Any], batch_size: int = 100) -> Iterable[List[Any]]:
    """Yield items in batches."""

    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


# Before we upload vectors, we need an index with the correct dimensionality.
# The dimensionality must match the embedding model output.
#
# For example:
# - some embedding models return 384 dimensions
# - others return 768, 1024, or 1536 dimensions
#
# If the Pinecone index dimension does not match the embedding dimension,
# the upsert will fail.
def create_or_get_index(vector_dimension: int):
    """Create Pinecone index if it does not exist, then return it."""
    cfg = get_config()
    logger.info("Using Pinecone index: %s", cfg.index_name)
    return get_pinecone_index(dimension=vector_dimension)


# Pinecone stores each vector as:
#
# ID:
#   A stable identifier for the chunk.
#
# values:
#   The embedding vector generated from the chunk content.
#
# metadata:
#   Structured information attached to the vector.
#   This allows filters like:
#   status = "Active"
#   plan = "Plan A"
#   region = "British Columbia"
#
# This is what makes production RAG more reliable than plain similarity search.
# We are not only asking:
# "Which text is semantically similar?"
#
# We are asking:
# "Which active, relevant, policy-approved text should be used as evidence?"
def build_vectors(chunks: List[Dict[str, Any]], embeddings) -> List[Dict[str, Any]]:
    """Prepare vectors for Pinecone upsert."""

    vectors = []

    for i, chunk in enumerate(chunks):
        metadata = {
            key: value
            for key, value in chunk.items()
            if key != "chunk_id"
        }

        vectors.append(
            {
                "id": chunk["chunk_id"],
                "values": embeddings[i].tolist(),
                "metadata": metadata,
            }
        )

    return vectors


def main() -> None:
    cfg = get_config()
    model = get_embedding_model()

    # Step 1:
    # Validate input documents before creating embeddings.
    # This avoids spending compute on documents that cannot be safely retrieved later.
    validate_policy_docs(policy_docs)

    # Step 2:
    # Convert policy documents into smaller, searchable chunks.
    all_chunks = []

    for doc in policy_docs:
        chunks = chunk_document(
            doc_text=doc["text"],
            metadata=doc["metadata"],
        )
        all_chunks.extend(chunks)

    unique_ids = {chunk["chunk_id"] for chunk in all_chunks}
    logger.info(
        "Generated %s chunks (%s unique IDs) from %s documents",
        len(all_chunks),
        len(unique_ids),
        len(policy_docs),
    )
    if len(unique_ids) != len(all_chunks):
        logger.warning(
            "Detected %s duplicate chunk IDs (will overwrite on upsert).",
            len(all_chunks) - len(unique_ids),
        )

    # Step 3:
    # Extract only the text content for embedding generation.
    # Metadata is not embedded here; it is stored separately for filtering.
    chunk_texts = [chunk["content"] for chunk in all_chunks]

    # Step 4:
    # Generate embeddings.
    # Each chunk becomes a dense vector that represents its semantic meaning.
    embeddings = model.encode(
        chunk_texts,
        show_progress_bar=True,
    )

    vector_dimension = embeddings.shape[1]

    logger.info("Generated embeddings with shape: %s", embeddings.shape)
    logger.info("Using index: %s", cfg.index_name)
    logger.info("Vector dimension: %s", vector_dimension)

    # Step 5:
    # Create or connect to the vector index.
    index = create_or_get_index(vector_dimension)

    # Step 6:
    # Convert chunks + embeddings into Pinecone's vector format.
    vectors_to_upsert = build_vectors(all_chunks, embeddings)

    # Step 7:
    # Upsert vectors in batches.
    #
    # The namespace acts like a logical partition.
    # It lets you separate environments, datasets, versions, or tenants.
    #
    # Example namespaces:
    # - bc-health-policy-v1
    # - bc-health-policy-v2
    # - customer-a-production
    # - customer-a-staging
    for batch in batch_items(vectors_to_upsert, batch_size=100):
        index.upsert(
            vectors=batch,
            namespace=cfg.namespace,
        )

    # Step 8:
    # Verify that indexing completed.
    stats = index.describe_index_stats()

    logger.info("Indexing completed.")
    namespaces = stats.get("namespaces") or {}
    ns_count = (namespaces.get(cfg.namespace) or {}).get("vector_count")
    logger.info("Vectors in namespace '%s': %s", cfg.namespace, ns_count)
    logger.info("Total vectors in index: %s", stats.get("total_vector_count"))


if __name__ == "__main__":
    main()
