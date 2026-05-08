# Healthcare Policy Assistant

A production-minded Retrieval-Augmented Generation (RAG) system for healthcare policy Q&A, built with Pinecone, OpenAI, and sentence-transformers.

This repository accompanies a two-part article series on building reliable RAG systems — from architecture to working implementation.

| | |
|---|---|
| **Part 1 — Architecture** | [Production RAG: The Architecture Behind Reliable Retrieval Systems](https://medium.com/@aldenirf/production-rag-the-architecture-behind-reliable-retrieval-systems-4161b940dae5) |
| **Part 2 — Implementation** | [Production RAG: Building Reliable Retrieval Systems](https://medium.com/@aldenirf/production-rag-building-a-reliable-retrieval-systems-5eb4f0f7f441) |

---

## How It Works

![RAG diagram](RAG%20-%20diagram.png)

The system runs in two phases:

**Phase 1 — Indexing** (`indexing_pipeline.py`)
Policy documents are validated, chunked with overlap, embedded using a biomedical sentence-transformer, and upserted into a Pinecone namespace with full metadata.

**Phase 2 — Retrieval & Generation** (`index_search.py` + `answer.py`)
A user question is embedded, filtered by metadata (status, plan, region), searched against the vector index, reranked, and passed to the LLM with a grounding instruction that restricts answers to retrieved evidence only.

---

## Project Structure

```
├── .env                    # API keys (see Setup)
├── requirements.txt        # Python dependencies
├── settings.py             # Shared config: clients, models, index name
├── policy.py               # Synthetic healthcare policy dataset (21 sections)
├── indexing_pipeline.py    # Chunk → embed → upsert into Pinecone
├── index_search.py         # Query → filter → search → rerank → evidence
└── answer.py               # Grounded generation with source citation
```

---

## Setup

**1. Clone and create a virtual environment**

```bash
git clone https://github.com/your-username/healthcare-policy-assistant.git
cd healthcare-policy-assistant

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment variables**

Copy the example file and fill in your keys:

```bash
cp .env_example .env
```

```dotenv
# .env
PINECONE_API_KEY=pcsk_...
OPENAI_API_KEY=sk-proj-...
```

You need a [Pinecone account](https://pinecone.io) (free tier works) and an [OpenAI account](https://platform.openai.com).

---

## Running the System

### Step 1 — Index the documents

Validates, chunks, embeds, and upserts all policy sections into Pinecone.

```bash
python indexing_pipeline.py
```

Expected output:

```
Generated 48 chunks from 21 documents
Generated embeddings with shape: (48, 768)
Using index: healthcare-policies
Vector dimension: 768
Indexing completed.
Total vectors in index: 48
```

Run this once. Re-running is safe — chunk IDs are deterministic (content-hashed), so Pinecone will upsert rather than duplicate.

### Step 2 — Ask questions

```bash
python answer.py
```

The script runs five test questions against active Plan A policies in British Columbia and prints answers with source citations.

---

## Example Output

```
==================================================
QUESTION: Does physical therapy require prior authorization?

ANSWER: Physical therapy sessions do not require prior authorization for up to
20 sessions annually when medically necessary. However, additional physiotherapy
sessions beyond 20 annually require prior authorization.

SOURCES:
- Policy POL-2026-0042, Section: PRIOR AUTHORIZATION,      Relevance: 0.93
- Policy POL-2026-0042, Section: PHYSIOTHERAPY COVERAGE,   Relevance: 0.91
- Policy POL-2026-0042, Section: DIAGNOSTIC IMAGING,       Relevance: 0.90

==================================================
QUESTION: Is physiotherapy covered after knee surgery?

ANSWER: Yes, physiotherapy is covered after knee surgery. Rehabilitation following
knee surgery includes up to 30 sessions when prescribed by a surgeon (Section 5).
Physiotherapy is covered when medically necessary, with up to 20 annual sessions
and additional sessions requiring prior authorization (Section 4). Home physiotherapy
is also covered for patients with limited mobility after surgery (Section 15).

SOURCES:
- Policy POL-2026-0042, Section: POST-SURGICAL REHABILITATION,  Relevance: 0.94
- Policy POL-2026-0042, Section: HOME REHABILITATION,           Relevance: 0.93
- Policy POL-2026-0042, Section: PHYSIOTHERAPY COVERAGE,        Relevance: 0.92

==================================================
QUESTION: Is my annual wellness visit covered at 100%?

ANSWER: Yes, your annual wellness visit is covered at 100% when provided once per
calendar year by an approved in-network primary care provider, according to
Policy POL-2026-0042, Section 21.

SOURCES:
- Policy POL-2026-0042, Section: PREVENTIVE CARE AND WELLNESS VISITS,  Relevance: 0.94
- Policy POL-2026-0042, Section: PRIMARY CARE VISITS,                  Relevance: 0.90
- Policy POL-2026-0042, Section: PHYSIOTHERAPY COVERAGE,               Relevance: 0.88
```

When no evidence clears the retrieval threshold, the system refuses rather than hallucinating:

```
ANSWER: I couldn't find specific information about that in our policy documents.
```

---

## Configuration

All defaults can be overridden via environment variables.

| Variable | Default | Description |
|---|---|---|
| `PINECONE_API_KEY` | — | **Required.** Pinecone API key |
| `OPENAI_API_KEY` | — | **Required.** OpenAI API key |
| `PINECONE_INDEX_NAME` | `healthcare-policies` | Pinecone index name |
| `PINECONE_NAMESPACE` | `health-policy-v1` | Namespace for logical isolation |
| `PINECONE_CLOUD` | `aws` | Cloud provider for serverless spec |
| `PINECONE_REGION` | `us-east-1` | Region for serverless spec |
| `OPENAI_MODEL` | `gpt-4.1-mini` | LLM used for generation |
| `EMBEDDING_MODEL_ID` | `pritamdeka/S-PubMedBert-MS-MARCO` | Sentence-transformer for embeddings |

---

## Key Design Decisions

**Deterministic chunk IDs** — Chunk IDs are SHA-256 hashes of content + metadata. Re-indexing updates existing vectors instead of creating duplicates.

**Domain embedding model** — `S-PubMedBert-MS-MARCO` is fine-tuned on biomedical literature and passage retrieval. It understands that *physiotherapy*, *physical therapy*, and *post-surgical rehabilitation* are semantically related.

**Metadata filtering before search** — Filters (`status=Active`, `plan=Plan A`, `region=British Columbia`) are applied at the database level before similarity search runs. Superseded or ineligible policy versions are excluded entirely, not ranked lower.

**Candidate expansion + reranking** — The pipeline retrieves `top_k=10` candidates, applies a minimum score threshold (`0.35`), reranks by a hybrid similarity + lexical signal, and delivers `final_k=3` chunks to the LLM.

**Grounded generation** — The LLM is instructed to answer only from retrieved excerpts. `temperature=0.1`, `top_p=0.3`, and `max_tokens=250` reduce variance and drift.

---

## License

MIT