from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from index_search import search_policies
from settings import get_config, get_openai_client


class Source(TypedDict):
    policy_id: str
    section: str
    relevance_score: float


class AnswerResult(TypedDict):
    answer: str
    sources: List[Source]


def answer_policy_question(
    query: str, filters: Optional[Dict[str, Any]] = None, *, top_k: int = 10, final_k: int = 3
) -> AnswerResult:
    """
    Retrieve grounded evidence from Pinecone and generate an answer using OpenAI.

    The model is instructed to answer only from retrieved excerpts.
    """
    cfg = get_config()
    client = get_openai_client()

    results = search_policies(query, filters, top_k=top_k, final_k=final_k)

    if not results:
        return {
            "answer": "I couldn't find specific information about that in our policy documents.",
            "sources": [],
        }

    context_parts: List[str] = []
    sources: List[Source] = []
    for i, result in enumerate(results, start=1):
        context_parts.append(
            f"POLICY EXCERPT {i} (Policy {result['policy_id']}):\n{result['content']}".strip()
        )
        sources.append(
            {
                "policy_id": result["policy_id"],
                "section": result["section_title"],
                "relevance_score": float(result["score"]),
            }
        )

    context = "\n\n".join(context_parts)

    prompt = (
        "Answer the question based ONLY on the provided policy excerpts.\n"
        "If the answer is not supported by the excerpts, say you don't have enough information.\n\n"
        f"POLICY EXCERPTS:\n{context}\n\n"
        f"QUESTION: {query}\n\n"
        "ANSWER:"
    )

    response = client.chat.completions.create(
        model=cfg.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a careful healthcare policy assistant that only answers from provided evidence.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        top_p=0.3,
        max_tokens=250,
    )

    answer_text = (response.choices[0].message.content or "").strip()

    return {"answer": answer_text, "sources": sources}


if __name__ == "__main__":
    questions = [
        "How many physiotherapy sessions are covered?",
        "Do I need prior authorization for an MRI?",
        "Are experimental procedures covered?",
    ]

    filters = {"status": "Active", "plan": "Plan A", "region": "British Columbia"}

    for question in questions:
        print("\n" + "=" * 50)
        print(f"QUESTION: {question}")
        response = answer_policy_question(question, filters=filters)
        print(f"\nANSWER: {response['answer']}")
        print("\nSOURCES:")
        for source in response["sources"]:
            print(
                f"- Policy {source['policy_id']}, "
                f"Section: {source['section']}, "
                f"Relevance: {source['relevance_score']:.2f}"
            )
