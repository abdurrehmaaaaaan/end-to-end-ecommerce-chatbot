"""
Streamlit chat ui for the priceoye laptops chatbot. Routes each query
to sql retrieval, faq retrieval, or both, using the semantic router.
No agents or tool-calling, routing and retrieval are plain function
calls chained together in this file.
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st

from router.semantic_router import SemanticRouter
from retrieval.sql_retriever import run_sql_query
from retrieval.faq_retriever import FAQRetriever
from memory.conversation_memory import ConversationMemory

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

st.set_page_config(page_title="Laptop Store Assistant", page_icon="💻")


# cached resources
@st.cache_resource
def load_router():
    return SemanticRouter()


@st.cache_resource
def load_faq_retriever():
    return FAQRetriever()


router = load_router()
faq_retriever = load_faq_retriever()

if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debug_log" not in st.session_state:
    st.session_state.debug_log = []


def format_sql_results(sql_result):
    rows = sql_result["results"]
    if not rows:
        return "No laptops matched that search."
    lines = []
    for r in rows:
        spec_bits = []
        if r["cpu"]:
            spec_bits.append(r["cpu"])
        if r["ram_gb"]:
            spec_bits.append(f"{r['ram_gb']}GB RAM")
        if r["storage"]:
            spec_bits.append(r["storage"])
        if r["gpu"]:
            spec_bits.append(r["gpu"])
        spec_text = ", ".join(spec_bits)
        lines.append(f"- {r['name']} ({r['brand']}) - Rs {r['price']:,} - {spec_text}")
    return "\n".join(lines)


def format_faq_results(faq_result):
    matches = faq_result["matches"]
    if not matches:
        return "I could not find a policy answer for that."
    lines = [m["answer"] for m in matches]
    return "\n\n".join(lines)


def synthesize_with_groq(user_query, sql_text, faq_text):
    # optional natural language phrasing step, only used to rewrite
    # already retrieved content, never used to decide routing or
    # retrieval, so this stays outside the agent/tool-calling boundary
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        context_parts = []
        if sql_text:
            context_parts.append(f"Product results:\n{sql_text}")
        if faq_text:
            context_parts.append(f"Policy info:\n{faq_text}")
        context_block = "\n\n".join(context_parts)

        prompt = (
            "You are a laptop store assistant. Using only the information "
            "below, answer the customer question in a short, friendly reply. "
            "Do not invent facts not present below.\n\n"
            f"Customer question: {user_query}\n\n{context_block}"
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400,
        )
        return response.choices[0].message.content
    except Exception:
        return None


def handle_query(user_query):
    context = st.session_state.memory.get_context_string()
    route_result = router.route(user_query, context=context)
    decision = route_result["decision"]

    sql_result = None
    faq_result = None

    if decision in ("SQL", "BOTH"):
        sql_result = run_sql_query(user_query)

    if decision in ("FAQ", "BOTH"):
        faq_result = faq_retriever.retrieve(user_query, context=context)

    sql_text = format_sql_results(sql_result) if sql_result else ""
    faq_text = format_faq_results(faq_result) if faq_result else ""

    final_answer = synthesize_with_groq(user_query, sql_text, faq_text)
    if final_answer is None:
        parts = []
        if sql_text:
            parts.append("Here are some laptops that match:\n" + sql_text)
        if faq_text:
            parts.append(faq_text)
        final_answer = "\n\n".join(parts) if parts else "I could not find an answer for that."

    debug_entry = {
        "query": user_query,
        "context_used": context,
        "route_decision": decision,
        "route_scores": route_result["scores"],
        "sql_filters": sql_result["filters"] if sql_result else None,
        "sql_query": sql_result["sql"] if sql_result else None,
        "faq_matches": faq_result["matches"] if faq_result else None,
    }

    return final_answer, debug_entry


# sidebar
with st.sidebar:
    st.header("Settings")
    debug_mode = st.checkbox("Show debug view", value=True)
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.debug_log = []
        st.session_state.memory.clear()
        st.rerun()

st.title("Laptop Store Assistant")
st.caption("Ask about laptops or store policies")

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and debug_mode and i // 2 < len(st.session_state.debug_log):
            debug_entry = st.session_state.debug_log[i // 2]
            with st.expander("Debug info"):
                st.json(debug_entry)

user_input = st.chat_input("Ask about a laptop or store policy")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, debug_entry = handle_query(user_input)
        st.markdown(answer)
        if debug_mode:
            with st.expander("Debug info"):
                st.json(debug_entry)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.debug_log.append(debug_entry)
    st.session_state.memory.add_turn(user_input, answer)