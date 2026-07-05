"""
LLM client wrapper for Groq Llama 3.3 70B, used to generate answers from
retrieved context (the "generation" half of RAG).

Requires GROQ_API_KEY set as an environment variable (use a .env file with
python-dotenv locally; never commit the key itself).
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_MODEL = "llama-3.3-70b-versatile"


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found. Set it in a .env file or environment variable."
        )
    return Groq(api_key=api_key)


def generate_answer(question: str, context_chunks: list, model: str = _MODEL) -> str:
    """
    Generate an answer to `question` grounded in `context_chunks` (a list of
    retrieved document strings). This is the RAG generation step: the model
    is instructed to answer ONLY from the provided context, reducing
    hallucination versus an ungrounded LLM call.
    """
    client = get_client()

    context_text = "\n".join(f"- {chunk}" for chunk in context_chunks)
    prompt = f"""Answer the question using ONLY the context below. If the context
doesn't contain enough information to answer, say so explicitly instead of guessing.

Context:
{context_text}

Question: {question}

Answer:"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500,
    )
    return response.choices[0].message.content