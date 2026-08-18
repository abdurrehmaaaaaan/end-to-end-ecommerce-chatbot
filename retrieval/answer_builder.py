import os
from groq import Groq

GROQ_MODEL = "llama-3.3-70b-versatile"


def format_sql_results(rows):
    # format product rows
    if not rows:
        return "No matching laptops found."
    lines = []
    for r in rows:
        stock = "in stock" if r["in_stock"] else "out of stock"
        lines.append(
            f"{r['name']} - Rs {r['price']} - {r['cpu'] or 'n/a'} - "
            f"{r['ram'] or 'n/a'} RAM - {stock}"
        )
    return "\n".join(lines)


def format_faq_results(matches):
    # format faq matches
    if not matches:
        return "No matching policy information found."
    lines = [m["answer"] for m in matches]
    return "\n".join(lines)


def build_raw_answer(route, sql_result, faq_result):
    # build template answer
    parts = []
    if route in ("SQL", "BOTH") and sql_result is not None:
        parts.append(format_sql_results(sql_result["results"]))
    if route in ("FAQ", "BOTH") and faq_result is not None:
        parts.append(format_faq_results(faq_result["matches"]))
    return "\n\n".join(parts)


def phrase_with_groq(query, raw_answer, memory_context):
    # phrase answer naturally
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return raw_answer

    client = Groq(api_key=api_key)
    system_prompt = (
        "You are a laptop store assistant. Answer using only the "
        "provided facts. Do not invent information. Keep it short."
    )
    user_prompt = (
        f"Conversation so far: {memory_context}\n"
        f"Question: {query}\n"
        f"Facts:\n{raw_answer}\n"
        f"Answer the question using the facts above."
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    return response.choices[0].message.content


def generate_answer(query, route, sql_result, faq_result, memory_context, use_groq=True):
    raw_answer = build_raw_answer(route, sql_result, faq_result)
    if not raw_answer.strip():
        return "I could not find relevant information for that."

    if use_groq:
        try:
            return phrase_with_groq(query, raw_answer, memory_context)
        except Exception:
            return raw_answer
    return raw_answer
