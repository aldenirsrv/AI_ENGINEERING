from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class AppConfig:
    pinecone_api_key: str
    openai_api_key: str
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    index_name: str = "healthcare-policies"
    openai_model: str = "gpt-4.1-mini"
    embedding_model_id: str = "pritamdeka/S-PubMedBert-MS-MARCO"
    namespace: str = "health-policy-v1"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """
    Load configuration from environment variables.

    This is intentionally lazy (called on demand) so importing modules doesn't
    immediately require external dependencies or valid secrets.
    """
    load_dotenv()

    return AppConfig(
        pinecone_api_key=_require_env("PINECONE_API_KEY"),
        openai_api_key=_require_env("OPENAI_API_KEY"),
        pinecone_cloud=os.environ.get("PINECONE_CLOUD", "aws"),
        pinecone_region=os.environ.get("PINECONE_REGION", "us-east-1"),
        index_name=os.environ.get("PINECONE_INDEX_NAME", "healthcare-policies"),
        openai_model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
        embedding_model_id=os.environ.get(
            "EMBEDDING_MODEL_ID", "pritamdeka/S-PubMedBert-MS-MARCO"
        ),
        namespace=os.environ.get("PINECONE_NAMESPACE", "health-policy-v1"),
    )


@lru_cache(maxsize=1)
def get_embedding_model():
    """Return the embedding model (cached)."""
    cfg = get_config()
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: sentence-transformers. "
            "Install it with `pip install sentence-transformers`."
        ) from exc

    return SentenceTransformer(cfg.embedding_model_id)


@lru_cache(maxsize=1)
def get_openai_client():
    """Return the OpenAI client (cached)."""
    cfg = get_config()
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: openai. Install it with `pip install openai`."
        ) from exc

    return OpenAI(api_key=cfg.openai_api_key)


@lru_cache(maxsize=1)
def get_pinecone_client():
    """Return the Pinecone client (cached)."""
    cfg = get_config()
    try:
        from pinecone import Pinecone
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: pinecone. Install it with `pip install pinecone`."
        ) from exc

    return Pinecone(api_key=cfg.pinecone_api_key)


def get_pinecone_spec():
    """Return a ServerlessSpec for creating Pinecone indexes."""
    cfg = get_config()
    try:
        from pinecone import ServerlessSpec
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: pinecone. Install it with `pip install pinecone`."
        ) from exc

    return ServerlessSpec(cloud=cfg.pinecone_cloud, region=cfg.pinecone_region)


def get_pinecone_index(*, dimension: int | None = None):
    """
    Return a Pinecone Index.

    If the index does not exist, `dimension` must be provided so it can be created.
    """
    cfg = get_config()
    pc = get_pinecone_client()

    existing = pc.list_indexes().names()
    if cfg.index_name not in existing:
        if dimension is None:
            raise RuntimeError(
                f"Pinecone index '{cfg.index_name}' does not exist. "
                "Run the indexing pipeline first."
            )
        pc.create_index(
            name=cfg.index_name,
            dimension=dimension,
            metric="cosine",
            spec=get_pinecone_spec(),
        )

    return pc.Index(cfg.index_name)

