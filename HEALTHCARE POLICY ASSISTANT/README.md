# Healthcare Policy Assistant (RAG Demo)

Minimal retrieval-augmented generation (RAG) example for healthcare policy Q&A:

- `policy.py` contains a small synthetic policy dataset.
- `indexing_pipeline.py` chunks + embeds policies and upserts them into Pinecone.
- `index_search.py` retrieves grounded evidence with optional metadata filters.
- `answer.py` generates an answer **only** from retrieved excerpts.

## RAG Diagram

![RAG diagram](RAG%20-%20diagram.webp)

## Setup

1. Create a `.env` file from `.env_example` and fill in keys.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Index the documents

```bash
python indexing_pipeline.py
```

## Ask questions

```bash
python answer.py
```

## Configuration

Environment variables (with defaults):

- `PINECONE_API_KEY` (required)
- `OPENAI_API_KEY` (required)
- `PINECONE_INDEX_NAME` (default: `healthcare-policies`)
- `PINECONE_NAMESPACE` (default: `health-policy-v1`)
- `PINECONE_CLOUD` (default: `aws`)
- `PINECONE_REGION` (default: `us-east-1`)
- `OPENAI_MODEL` (default: `gpt-4.1-mini`)
- `EMBEDDING_MODEL_ID` (default: `pritamdeka/S-PubMedBert-MS-MARCO`)
