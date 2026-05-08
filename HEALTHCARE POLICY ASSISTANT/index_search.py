# index_search.py
import logging
from typing import Any, Dict, List, Optional

from settings import get_config, get_embedding_model, get_pinecone_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_filter(filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    # Step 1:
    # Build metadata filters.
    #
    # Metadata filtering is one of the most important differences
    # between naive RAG and production-minded RAG.
    #
    # Without filters, the system may retrieve:
    # - outdated policies
    # - inactive documents
    # - wrong plans
    # - wrong regions
    #
    # Example:
    # filters = {
    #     "status": "Active",
    #     "plan": "Plan A",
    #     "region": "British Columbia"
    # }
    if not filters:
        return None

    return {key: {"$eq": value} for key, value in filters.items()}


def simple_rerank(query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Step 5:
    # Rerank retrieved candidates.
    #
    # Vector search is good at finding semantically similar text,
    # but the highest vector score is not always the best evidence.
    #
    # Reranking gives the system a second chance to sort the results
    # based on stronger relevance signals.
    #
    # For article purposes, this function uses a lightweight lexical reranker.
    # In real production systems, this is usually replaced by:
    # - a cross-encoder reranker
    # - a domain-specific reranker
    # - an LLM-based evidence evaluator

    query_terms = set(query.lower().split())

    for candidate in candidates:
        content = candidate.get("content", "").lower()
        section = candidate.get("section_title", "").lower()

        lexical_score = sum(
            1 for term in query_terms
            if term in content or term in section
        )

        candidate["rerank_score"] = (
            candidate["score"] * 0.75
            + lexical_score * 0.25
        )

    return sorted(
        candidates,
        key=lambda item: item["rerank_score"],
        reverse=True,
    )


def format_evidence(result: Dict[str, Any], position: int) -> Dict[str, Any]:
    # Step 6:
    # Format results as grounded evidence.
    #
    # The answer generator should not receive random chunks with no context.
    # It should receive structured evidence objects.
    #
    # Each evidence object includes:
    # - content: the text the model is allowed to use
    # - policy_id: where the evidence came from
    # - section_title: the policy section
    # - effective_date: which version applies
    # - status: whether the policy is active
    #
    # This makes the final answer more auditable and citation-ready.

    return {
        "evidence_id": f"E{position}",
        "score": round(result.get("score", 0), 4),
        "rerank_score": round(result.get("rerank_score", 0), 4),
        "policy_id": result.get("policy_id"),
        "section_title": result.get("section_title"),
        "category": result.get("category"),
        "department": result.get("department"),
        "plan": result.get("plan"),
        "region": result.get("region"),
        "effective_date": result.get("effective_date"),
        "status": result.get("status"),
        "content": result.get("content"),
        "citation": (
            f"{result.get('policy_id')} | "
            f"{result.get('section_title')} | "
            f"effective {result.get('effective_date')}"
        ),
    }


def search_policies(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 10,
    final_k: int = 3,
    min_score: float = 0.35,
) -> List[Dict[str, Any]]:
    """
    Production-minded retrieval pipeline.
    """

    # Step 0:
    # Validate the user query.
    #
    # A production system should fail early on invalid input.
    # Empty queries should not be embedded, searched, or sent to the model.
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    # Step 1:
    # Generate an embedding for the user query.
    #
    # The embedding converts natural language into a dense vector.
    # Pinecone uses this vector to find policy chunks with similar meaning.
    cfg = get_config()
    model = get_embedding_model()
    index = get_pinecone_index()

    query_embedding = model.encode([query])[0].tolist()

    # Step 2:
    # Build metadata filters.
    #
    # This limits retrieval to approved evidence.
    # For example, we can search only:
    # - active policies
    # - Plan A
    # - British Columbia
    filter_dict = build_filter(filters)

    # Step 3:
    # Retrieve more candidates than we need.
    #
    # Naive RAG often retrieves top_k=3 and directly sends those chunks
    # to the language model.
    #
    # Production-minded RAG usually retrieves more candidates first,
    # then reranks them.
    #
    # Example:
    # - retrieve top_k=10
    # - rerank candidates
    # - keep final_k=3
    query_results = index.query(
        vector=query_embedding,
        filter=filter_dict,
        top_k=top_k,
        namespace=cfg.namespace,
        include_metadata=True,
    )

    # Step 4:
    # Convert raw vector matches into candidate evidence.
    #
    # We also apply a minimum score threshold.
    # This prevents weak matches from reaching the answer generator.
    #
    # The threshold should be tuned with evaluation data.
    # A value that works for one dataset may be too strict or too loose
    # for another dataset.
    candidates = []

    for match in query_results.get("matches", []):
        score = match.get("score", 0)

        if score < min_score:
            continue

        metadata = match.get("metadata", {})

        candidates.append(
            {
                "score": score,
                "content": metadata.get("content", ""),
                "section_title": metadata.get("section_title"),
                "policy_id": metadata.get("policy_id"),
                "category": metadata.get("category"),
                "department": metadata.get("department"),
                "plan": metadata.get("plan"),
                "region": metadata.get("region"),
                "effective_date": metadata.get("effective_date"),
                "status": metadata.get("status"),
            }
        )

    # Step 5:
    # If no reliable candidate is found, return no evidence.
    #
    # This is safer than forcing the model to answer without support.
    if not candidates:
        return []

    # Step 6:
    # Rerank candidates.
    #
    # The goal is to improve evidence ordering before generation.
    # This reduces the risk of sending less relevant chunks to the model.
    reranked_candidates = simple_rerank(query, candidates)

    # Step 7:
    # Keep only the strongest evidence chunks.
    #
    # The final context should be focused.
    # Too many chunks can confuse the model and increase cost.
    final_results = reranked_candidates[:final_k]

    # Step 8:
    # Return citation-ready evidence.
    #
    # The final answer should be generated only from this evidence.
    # This makes the system more grounded, auditable, and easier to debug.
    return [
        format_evidence(result, position=i)
        for i, result in enumerate(final_results, start=1)
    ]
