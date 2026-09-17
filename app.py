import json
import streamlit as st
import agent
import guardrails as G
from audit_log import read_log

st.set_page_config(page_title="Customer Resolution Agent", page_icon="✈️")
st.title("✈️ Customer Resolution Agent")
st.caption("Airline disruption support — powered strictly by the supplied data pack and service rules.")

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("🔧 Audit Trail")
    st.caption("Every action, with the rule cited. Append-only JSONL: audit_log.jsonl")
    for rec in reversed(read_log(25)):
        icon = "🚨" if rec["escalation"] else "✅"
        st.markdown(
            f"{icon} **{rec['action']}** — {rec['customer']}  \n"
            f"`{rec['rule_cited']}`  \n"
            f"<small>{rec['outcome']} · {rec['timestamp']}</small>",
            unsafe_allow_html=True,
        )
    if st.button("🗑 Reset conversation"):
        st.session_state.history = []
        st.rerun()

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.write(m["content"])

user_input = st.chat_input("Type your message as the customer…")
if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Deterministic guardrail: legal/formal-complaint triggers immediate escalation
    if G.needs_escalation(user_input):
        st.session_state.history.append({
            "role": "system_note",
            "content": "DETERMINISTIC GUARDRAIL TRIGGERED: the customer mentioned legal action or a formal complaint. You must call escalate_to_human immediately.",
        })

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            # build a clean message list for the LLM (system_note folded into user turn)
            llm_history = []
            for m in st.session_state.history:
                if m["role"] == "system_note":
                    if llm_history:
                        llm_history[-1]["content"] += "\n\n[" + m["content"] + "]"
                else:
                    llm_history.append({"role": m["role"], "content": m["content"]})
            reply = agent.get_reply(llm_history)
            st.write(reply)
    st.session_state.history.append({"role": "assistant", "content": reply})