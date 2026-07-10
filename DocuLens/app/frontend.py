import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="DocuLens", page_icon="🔍", layout="centered")
st.title("🔍 DocuLens")
st.caption("Upload a PDF and ask questions about it.")

# ── Session state ─────────────────────────────────────────────────────────────
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar: upload ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📄 Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

    if uploaded_file and st.button("Upload", use_container_width=True):
        with st.spinner("Uploading and indexing…"):
            response = requests.post(
                f"{API_URL}/upload",
                files={"file": (uploaded_file.name, uploaded_file, "application/pdf")},
            )
        if response.ok:
            st.session_state.chat_id = response.json()["chat_id"]
            st.session_state.messages = []
            st.success("PDF ready! Ask away.")
        else:
            st.error(response.json().get("detail", "Upload failed"))

    if st.session_state.chat_id:
        st.divider()
        if st.button("📝 Summarize PDF", use_container_width=True):
            with st.spinner("Summarizing…"):
                resp = requests.post(
                    f"{API_URL}/summarize",
                    params={"chat_id": st.session_state.chat_id},
                )
            if resp.ok:
                summary = resp.json()["summary"]
                st.session_state.messages.append({"role": "assistant", "content": summary})
                st.rerun()
            else:
                st.error("Summarization failed")

# ── Chat area ─────────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(
    "Ask something about your PDF…",
    disabled=not st.session_state.chat_id,
):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            resp = requests.post(
                f"{API_URL}/chat",
                params={"chat_id": st.session_state.chat_id},
                json={"question": prompt},
            )
        if resp.ok:
            answer = resp.json()["answer"]
        else:
            answer = f"Error: {resp.json().get('detail', 'Something went wrong')}"

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})