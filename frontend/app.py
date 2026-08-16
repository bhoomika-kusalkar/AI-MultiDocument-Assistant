import streamlit as st
import requests


# =========================================================
# CONFIGURATION
# =========================================================

BACKEND_URL = "http://127.0.0.1:8000"


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI PDF Chatbot",
    page_icon="🤖",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("🤖 AI Multi-Document Chatbot")

st.caption(
    "Upload multiple PDF documents and ask questions "
    "across all of them."
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("📚 Documents")

    # -----------------------------------------------------
    # Get currently loaded documents
    # -----------------------------------------------------

    try:

        response = requests.get(
            f"{BACKEND_URL}/documents",
            timeout=10
        )

        if response.status_code == 200:

            document_data = response.json()

            current_documents = document_data.get(
                "documents",
                []
            )

            total_documents = document_data.get(
                "total_documents",
                0
            )

            total_chunks = document_data.get(
                "total_chunks",
                0
            )

            st.write(
                f"📄 **Documents:** {total_documents}"
            )

            st.write(
                f"🧩 **Chunks:** {total_chunks}"
            )

            if current_documents:

                st.divider()

                for document in current_documents:

                    st.write(
                        f"📄 **{document['filename']}**"
                    )

                    st.caption(
                        f"{document['pages']} pages • "
                        f"{document['chunks']} chunks"
                    )

        else:

            st.warning(
                "Could not load document list."
            )

    except requests.exceptions.ConnectionError:

        st.error(
            "FastAPI backend is not running."
        )


# =========================================================
# UPLOAD DOCUMENTS
# =========================================================

st.subheader("📤 Upload Documents")

uploaded_files = st.file_uploader(
    "Choose one or more PDF files",
    type=["pdf"],
    accept_multiple_files=True
)


if uploaded_files:

    st.write(
        f"Selected **{len(uploaded_files)}** document(s):"
    )

    for file in uploaded_files:

        st.write(
            f"📄 {file.name}"
        )


    if st.button(
        "📤 Process Documents",
        use_container_width=True
    ):

        with st.spinner(
            "Processing documents and creating embeddings..."
        ):

            try:

                files = []

                for file in uploaded_files:

                    files.append(
                        (
                            "files",
                            (
                                file.name,
                                file.getvalue(),
                                "application/pdf"
                            )
                        )
                    )

                response = requests.post(
                    f"{BACKEND_URL}/upload",
                    files=files,
                    timeout=300
                )

                if response.status_code == 200:

                    data = response.json()

                    st.success(
                        "Documents processed successfully! 🎉"
                    )

                    uploaded = data.get(
                        "uploaded",
                        []
                    )

                    for document in uploaded:

                        st.write(
                            f"✅ **{document['filename']}** — "
                            f"{document['pages']} pages, "
                            f"{document['chunks']} chunks"
                        )

                    st.rerun()

                else:

                    st.error(
                        f"Upload failed:\n\n"
                        f"{response.text}"
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to FastAPI. "
                    "Make sure Uvicorn is running."
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The upload took too long. "
                    "Try a smaller PDF first."
                )

            except Exception as e:

                st.error(
                    f"Error: {str(e)}"
                )


# =========================================================
# CLEAR DOCUMENTS
# =========================================================

st.divider()

if st.button(
    "🗑️ Clear All Documents",
    use_container_width=True
):

    try:

        response = requests.delete(
            f"{BACKEND_URL}/documents",
            timeout=30
        )

        if response.status_code == 200:

            st.success(
                "All documents cleared."
            )

            st.rerun()

        else:

            st.error(
                response.text
            )

    except Exception as e:

        st.error(
            f"Error: {str(e)}"
        )


# =========================================================
# CHAT
# =========================================================

st.divider()

st.subheader("💬 Ask Your Documents")


# =========================================================
# CHAT HISTORY
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# Display previous messages

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

        if message.get("sources"):

            st.caption("📚 Sources")

            for source in message["sources"]:

                st.write(
                    f"📄 {source['document']} "
                    f"— Page {source['page']}"
                )


# =========================================================
# CHAT INPUT
# =========================================================

question = st.chat_input(
    "Ask something about your documents..."
)


if question:

    # -----------------------------------------------------
    # Display user question
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):

        st.markdown(question)


    # -----------------------------------------------------
    # Ask backend
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching your documents..."
        ):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/ask",
                    json={
                        "question": question
                    },
                    timeout=120
                )

                if response.status_code == 200:

                    data = response.json()

                    answer = data.get(
                        "answer",
                        "No answer received."
                    )

                    sources = data.get(
                        "sources",
                        []
                    )

                    # -----------------------------------------
                    # Answer
                    # -----------------------------------------

                    st.markdown(answer)

                    # -----------------------------------------
                    # Sources
                    # -----------------------------------------

                    if sources:

                        st.caption(
                            "📚 Sources"
                        )

                        for source in sources:

                            st.write(
                                f"📄 "
                                f"{source['document']} "
                                f"— Page "
                                f"{source['page']}"
                            )

                    # -----------------------------------------
                    # Save assistant message
                    # -----------------------------------------

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        }
                    )

                else:

                    error_message = (
                        f"Backend error: "
                        f"{response.text}"
                    )

                    st.error(
                        error_message
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to FastAPI. "
                    "Make sure Uvicorn is running."
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The AI request took too long."
                )

            except Exception as e:

                st.error(
                    f"Error: {str(e)}"
                )