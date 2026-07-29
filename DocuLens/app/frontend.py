import os
from typing import Any

import requests
import streamlit as st
from streamlit_cookies_controller import CookieController


# ── Configuration ─────────────────────────────────────────────────────────────

API_URL = os.getenv(
    "DOCULENS_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

TOKEN_COOKIE_NAME = "doculens_access_token"

REQUEST_TIMEOUT = 120


# ── Streamlit page configuration ──────────────────────────────────────────────

st.set_page_config(
    page_title="DocuLens",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Cookie controller ─────────────────────────────────────────────────────────

cookies = CookieController()


# ── Custom styling ────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 3.5rem;
            padding-bottom: 6rem;
            max-width: 1200px;
        }

        .doculens-title {
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1.25;
            overflow-wrap: anywhere;
            margin-top: 0;
            margin-bottom: 0.4rem;
        }

        .doculens-subtitle {
            color: #6b7280;
            margin-top: 0.2rem;
            margin-bottom: 1.5rem;
        }

        .welcome-box {
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 14px;
            padding: 2rem;
            text-align: center;
            margin-top: 2rem;
        }

        .small-muted {
            color: #6b7280;
            font-size: 0.9rem;
        }

        [data-testid="stSidebar"] {
            min-width: 280px;
            max-width: 340px;
        }

        /*
        Allow long button labels and chat names to wrap instead of
        being clipped.
        */
        div[data-testid="stButton"] button {
            min-height: 2.8rem;
            height: auto;
        }

        div[data-testid="stButton"] button p {
            white-space: normal;
            overflow-wrap: anywhere;
            line-height: 1.25;
        }

        /*
        Keep the chat input above the bottom edge.
        */
        [data-testid="stChatInput"] {
            padding-bottom: 0.5rem;
        }

        /*
        Improve responsiveness for smaller browser widths.
        */
        @media (max-width: 900px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .doculens-title {
                font-size: 1.8rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session state ─────────────────────────────────────────────────────────────

def initialize_session_state() -> None:
    defaults = {
        "access_token": None,
        "current_user": None,
        "selected_chat_id": None,
        "selected_chat_name": None,
        "new_chat_mode": False,
        "auth_checked": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_session_state()


# ── API helpers ───────────────────────────────────────────────────────────────

def get_auth_headers() -> dict[str, str]:
    token = st.session_state.access_token

    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}",
    }


def extract_error_message(
    response: requests.Response,
) -> str:
    try:
        data = response.json()

        detail = data.get("detail")

        if isinstance(detail, str):
            return detail

        if isinstance(detail, list):
            messages: list[str] = []

            for item in detail:
                if isinstance(item, dict):
                    message = item.get("msg")

                    if message:
                        messages.append(str(message))

            if messages:
                return ", ".join(messages)

        message = data.get("message")

        if isinstance(message, str):
            return message

    except ValueError:
        pass

    if response.text:
        return response.text

    return (
        f"Request failed with status code "
        f"{response.status_code}."
    )


def api_request(
    method: str,
    endpoint: str,
    *,
    json: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    authenticated: bool = True,
    timeout: int = REQUEST_TIMEOUT,
) -> requests.Response | None:
    url = f"{API_URL}{endpoint}"

    headers = (
        get_auth_headers()
        if authenticated
        else {}
    )

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            files=files,
            timeout=timeout,
        )

    except requests.ConnectionError:
        st.error(
            "Could not connect to the DocuLens backend. "
            "Make sure FastAPI is running on port 8000."
        )
        return None

    except requests.Timeout:
        st.error(
            "The request took too long. Please try again."
        )
        return None

    except requests.RequestException as error:
        st.error(
            f"Request failed: {error}"
        )
        return None

    if (
        response.status_code == 401
        and authenticated
    ):
        logout_user(
            show_message=False,
        )

        st.error(
            "Your session has expired. "
            "Please log in again."
        )

        return None

    return response


# ── Authentication helpers ────────────────────────────────────────────────────

def save_login(
    token: str,
) -> None:
    st.session_state.access_token = token

    cookies.set(
        TOKEN_COOKIE_NAME,
        token,
    )


def logout_user(
    show_message: bool = True,
) -> None:
    try:
        cookies.remove(
            TOKEN_COOKIE_NAME
        )

    except Exception:
        pass

    st.session_state.access_token = None
    st.session_state.current_user = None
    st.session_state.selected_chat_id = None
    st.session_state.selected_chat_name = None
    st.session_state.new_chat_mode = False
    st.session_state.auth_checked = True

    if show_message:
        st.success(
            "Logged out successfully."
        )


def load_current_user() -> bool:
    response = api_request(
        method="GET",
        endpoint="/auth/me",
    )

    if response is None:
        return False

    if response.ok:
        st.session_state.current_user = (
            response.json()
        )
        return True

    logout_user(
        show_message=False,
    )

    return False


def restore_login_from_cookie() -> None:
    if st.session_state.auth_checked:
        return

    st.session_state.auth_checked = True

    token = cookies.get(
        TOKEN_COOKIE_NAME
    )

    if not token:
        return

    st.session_state.access_token = token

    load_current_user()


restore_login_from_cookie()


# ── Chat API helpers ──────────────────────────────────────────────────────────

def fetch_chats() -> list[dict[str, Any]]:
    response = api_request(
        method="GET",
        endpoint="/chats",
    )

    if response is None:
        return []

    if not response.ok:
        st.error(
            extract_error_message(response)
        )
        return []

    data = response.json()

    if isinstance(data, list):
        return data

    return []


def fetch_messages(
    chat_id: str,
) -> list[dict[str, Any]]:
    response = api_request(
        method="GET",
        endpoint=f"/chats/{chat_id}/messages",
    )

    if response is None:
        return []

    if not response.ok:
        st.error(
            extract_error_message(response)
        )
        return []

    data = response.json()

    if isinstance(data, list):
        return data

    return []


def create_chat(
    chat_name: str,
) -> dict[str, Any] | None:
    response = api_request(
        method="POST",
        endpoint="/chats",
        json={
            "chat_name": chat_name,
        },
    )

    if response is None:
        return None

    if not response.ok:
        st.error(
            extract_error_message(response)
        )
        return None

    return response.json()


def delete_chat(
    chat_id: str,
) -> bool:
    response = api_request(
        method="DELETE",
        endpoint=f"/chats/{chat_id}",
    )

    if response is None:
        return False

    if response.status_code == 204:
        return True

    st.error(
        extract_error_message(response)
    )

    return False


def rename_chat(
    chat_id: str,
    new_name: str,
) -> dict[str, Any] | None:
    response = api_request(
        method="PATCH",
        endpoint=f"/chats/{chat_id}",
        json={
            "chat_name": new_name,
        },
    )

    if response is None:
        return None

    if not response.ok:
        st.error(
            extract_error_message(response)
        )
        return None

    return response.json()


def upload_pdf(
    chat_id: str,
    uploaded_file,
) -> dict[str, Any] | None:
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }

    response = api_request(
        method="POST",
        endpoint=f"/chats/{chat_id}/upload",
        files=files,
        timeout=300,
    )

    if response is None:
        return None

    if not response.ok:
        st.error(
            extract_error_message(response)
        )
        return None

    return response.json()


def ask_question(
    chat_id: str,
    question: str,
) -> dict[str, Any] | None:
    response = api_request(
        method="POST",
        endpoint=f"/chats/{chat_id}/ask",
        json={
            "question": question,
        },
        timeout=300,
    )

    if response is None:
        return None

    if not response.ok:
        st.error(
            extract_error_message(response)
        )
        return None

    return response.json()


def generate_summary(
    chat_id: str,
) -> dict[str, Any] | None:
    response = api_request(
        method="POST",
        endpoint=f"/chats/{chat_id}/summary",
        timeout=300,
    )

    if response is None:
        return None

    if not response.ok:
        st.error(
            extract_error_message(response)
        )
        return None

    return response.json()


# ── Authentication screen ─────────────────────────────────────────────────────

def render_authentication_screen() -> None:
    st.markdown(
        '<p class="doculens-title">🔍 DocuLens</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p class="doculens-subtitle">
            Upload PDF documents, generate summaries and ask
            context-aware questions.
        </p>
        """,
        unsafe_allow_html=True,
    )

    _, auth_column, _ = st.columns(
        [1, 1.5, 1]
    )

    with auth_column:
        login_tab, signup_tab = st.tabs(
            [
                "Login",
                "Create account",
            ]
        )

        with login_tab:
            with st.form(
                "login_form",
                clear_on_submit=False,
            ):
                login_email = st.text_input(
                    "Email",
                    placeholder="Enter your email",
                )

                login_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                )

                login_submitted = (
                    st.form_submit_button(
                        "Login",
                        use_container_width=True,
                    )
                )

            if login_submitted:
                email = login_email.strip()

                if (
                    not email
                    or not login_password
                ):
                    st.warning(
                        "Please enter your email "
                        "and password."
                    )

                else:
                    with st.spinner(
                        "Logging in..."
                    ):
                        response = api_request(
                            method="POST",
                            endpoint="/auth/login",
                            json={
                                "email": email,
                                "password": login_password,
                            },
                            authenticated=False,
                        )

                    if response is not None:
                        if response.ok:
                            data = response.json()

                            token = data.get(
                                "access_token"
                            )

                            if not token:
                                st.error(
                                    "The backend did not "
                                    "return an access token."
                                )

                            else:
                                save_login(token)

                                if load_current_user():
                                    st.success(
                                        "Login successful."
                                    )
                                    st.rerun()

                        else:
                            st.error(
                                extract_error_message(
                                    response
                                )
                            )

        with signup_tab:
            with st.form(
                "signup_form",
                clear_on_submit=False,
            ):
                signup_name = st.text_input(
                    "Full name",
                    placeholder="Enter your full name",
                )

                signup_username = st.text_input(
                    "Username",
                    placeholder="At least 6 characters",
                )

                signup_email = st.text_input(
                    "Email address",
                    placeholder="Enter your email",
                )

                signup_phone = st.text_input(
                    "Phone number",
                    placeholder="Enter your phone number",
                )

                signup_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a password",
                )

                signup_confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder=(
                        "Enter the password again"
                    ),
                )

                signup_submitted = (
                    st.form_submit_button(
                        "Create account",
                        use_container_width=True,
                    )
                )

            if signup_submitted:
                name = signup_name.strip()
                username = signup_username.strip()
                email = signup_email.strip()
                phone = signup_phone.strip()

                if not all(
                    [
                        name,
                        username,
                        email,
                        signup_password,
                    ]
                ):
                    st.warning(
                        "Please fill in all "
                        "required fields."
                    )

                elif len(username) < 6:
                    st.warning(
                        "Username must contain "
                        "at least 6 characters."
                    )

                elif (
                    signup_password
                    != signup_confirm_password
                ):
                    st.warning(
                        "Passwords do not match."
                    )

                else:
                    request_data = {
                        "name": name,
                        "username": username,
                        "email": email,
                        "phone_no": phone or None,
                        "password": signup_password,
                    }

                    with st.spinner(
                        "Creating your account..."
                    ):
                        response = api_request(
                            method="POST",
                            endpoint="/auth/signup",
                            json=request_data,
                            authenticated=False,
                        )

                    if response is not None:
                        if response.ok:
                            st.success(
                                "Account created successfully. "
                                "You can now log in."
                            )

                        else:
                            st.error(
                                extract_error_message(
                                    response
                                )
                            )


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> list[dict[str, Any]]:
    with st.sidebar:
        st.markdown(
            "## 🔍 DocuLens"
        )

        current_user = (
            st.session_state.current_user
            or {}
        )

        display_name = (
            current_user.get("name")
            or current_user.get("username")
            or "User"
        )

        st.caption(
            f"Signed in as {display_name}"
        )

        if st.button(
            "➕ New chat",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.selected_chat_id = None
            st.session_state.selected_chat_name = None
            st.session_state.new_chat_mode = True
            st.rerun()

        st.divider()

        st.markdown(
            "### Previous chats"
        )

        chats = fetch_chats()

        if not chats:
            st.caption(
                "No chats yet."
            )

        for chat in chats:
            chat_id = chat.get(
                "chat_id"
            )

            chat_name = chat.get(
                "chat_name",
                "Untitled chat",
            )

            if not chat_id:
                continue

            is_selected = (
                chat_id
                == st.session_state.selected_chat_id
            )

            button_type = (
                "primary"
                if is_selected
                else "secondary"
            )

            if st.button(
                f"📄 {chat_name}",
                key=f"chat_{chat_id}",
                use_container_width=True,
                type=button_type,
            ):
                st.session_state.selected_chat_id = (
                    chat_id
                )

                st.session_state.selected_chat_name = (
                    chat_name
                )

                st.session_state.new_chat_mode = False

                st.rerun()

        st.divider()

        if st.button(
            "Logout",
            use_container_width=True,
        ):
            logout_user()
            st.rerun()

    return chats


# ── Welcome screen ────────────────────────────────────────────────────────────

def render_welcome_screen() -> None:
    current_user = (
        st.session_state.current_user
        or {}
    )

    display_name = (
        current_user.get("name")
        or current_user.get("username")
        or "there"
    )

    st.markdown(
        (
            f'<p class="doculens-title">'
            f'Welcome, {display_name} 👋'
            f'</p>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="welcome-box">
            <h3>Start working with a PDF</h3>
            <p>
                Create a new chat and upload a PDF,
                or select one of your previous chats
                from the sidebar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "Create a new chat",
        type="primary",
    ):
        st.session_state.new_chat_mode = True
        st.rerun()


# ── New chat and upload screen ────────────────────────────────────────────────

def render_new_chat_screen() -> None:
    st.markdown(
        '<p class="doculens-title">New PDF chat</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p class="doculens-subtitle">
            Upload one PDF to create a new conversation.
        </p>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        accept_multiple_files=False,
    )

    if uploaded_file is not None:
        file_contents = (
            uploaded_file.getvalue()
        )

        file_size_mb = (
            len(file_contents)
            / (1024 * 1024)
        )

        st.caption(
            f"Selected: {uploaded_file.name} "
            f"({file_size_mb:.2f} MB)"
        )

    upload_clicked = st.button(
        "Upload and create chat",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
    )

    if (
        upload_clicked
        and uploaded_file is not None
    ):
        file_contents = (
            uploaded_file.getvalue()
        )

        if (
            len(file_contents)
            > 10 * 1024 * 1024
        ):
            st.error(
                "The PDF must not be larger "
                "than 10 MB."
            )
            return

        with st.spinner(
            "Creating chat, reading PDF and "
            "building the search index..."
        ):
            chat = create_chat(
                chat_name=uploaded_file.name,
            )

            if chat is None:
                return

            chat_id = chat.get(
                "chat_id"
            )

            if not chat_id:
                st.error(
                    "The backend did not return "
                    "a chat ID."
                )
                return

            upload_result = upload_pdf(
                chat_id=chat_id,
                uploaded_file=uploaded_file,
            )

            if upload_result is None:
                delete_chat(
                    chat_id
                )
                return

        st.session_state.selected_chat_id = (
            chat_id
        )

        st.session_state.selected_chat_name = (
            upload_result.get("pdf_name")
            or uploaded_file.name
        )

        st.session_state.new_chat_mode = False

        st.success(
            "PDF uploaded and indexed successfully."
        )

        st.rerun()


# ── Selected chat controls ────────────────────────────────────────────────────

def render_chat_controls(
    chat_id: str,
    chat_name: str,
) -> None:
    with st.expander(
        "Chat options",
        expanded=False,
    ):
        rename_column, delete_column = (
            st.columns(
                [3, 1.2]
            )
        )

        with rename_column:
            new_chat_name = st.text_input(
                "Chat name",
                value=chat_name,
                key=f"rename_input_{chat_id}",
            )

            if st.button(
                "Rename chat",
                key=f"rename_button_{chat_id}",
                use_container_width=True,
            ):
                cleaned_name = (
                    new_chat_name.strip()
                )

                if not cleaned_name:
                    st.warning(
                        "Chat name cannot be empty."
                    )

                else:
                    result = rename_chat(
                        chat_id=chat_id,
                        new_name=cleaned_name,
                    )

                    if result is not None:
                        st.session_state.selected_chat_name = (
                            result.get("chat_name")
                            or cleaned_name
                        )

                        st.success(
                            "Chat renamed."
                        )

                        st.rerun()

        with delete_column:
            st.write("")
            st.write("")

            confirm_delete = st.checkbox(
                "Confirm",
                key=f"confirm_delete_{chat_id}",
            )

            if st.button(
                "Delete",
                key=f"delete_button_{chat_id}",
                use_container_width=True,
                disabled=not confirm_delete,
            ):
                if delete_chat(
                    chat_id
                ):
                    st.session_state.selected_chat_id = None
                    st.session_state.selected_chat_name = None
                    st.session_state.new_chat_mode = False

                    st.success(
                        "Chat deleted."
                    )

                    st.rerun()


# ── Chat screen ───────────────────────────────────────────────────────────────

def render_chat_screen(
    chat_id: str,
    chat_name: str,
) -> None:
    st.markdown(
        """
        <style>
            .chat-header-spacer {
                height: 1.2rem;
            }
        </style>
        <div class="chat-header-spacer"></div>
        """,
        unsafe_allow_html=True,
    )

    title_column, summary_column = st.columns(
        [2.5, 1.5],
        gap="large",
        vertical_alignment="center",
    )

    with title_column:
        st.markdown(
            f"""
            <div style="
                font-size: 1.6rem;
                font-weight: 700;
                line-height: 1.3;
                overflow-wrap: anywhere;
                padding-top: 0.4rem;
                padding-bottom: 0.4rem;
            ">
                📄 {chat_name}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with summary_column:
        st.write("")

        summary_clicked = st.button(
            "📝 Generate summary",
            key=f"summary_button_{chat_id}",
            use_container_width=True,
        )

    st.write("")

    render_chat_controls(
        chat_id=chat_id,
        chat_name=chat_name,
    )

    if summary_clicked:
        with st.spinner(
            "Generating document summary..."
        ):
            summary_result = generate_summary(
                chat_id=chat_id,
            )

        if summary_result is not None:
            st.success(
                "Summary is ready."
            )
            st.rerun()

    messages = fetch_messages(chat_id)

    if not messages:
        st.info(
            "Your PDF is ready. Ask a question "
            "or generate a summary."
        )

    for message in messages:
        sender = str(
            message.get(
                "sent_by",
                "assistant",
            )
        ).lower()

        if "." in sender:
            sender = sender.split(".")[-1]

        role = (
            "user"
            if sender == "user"
            else "assistant"
        )

        content = str(
            message.get(
                "content",
                "",
            )
        )

        if not content.strip():
            continue

        with st.chat_message(role):
            st.markdown(content)

    question = st.chat_input(
        "Ask a question about this PDF...",
        key=f"chat_input_{chat_id}",
    )

    if question:
        cleaned_question = question.strip()

        if not cleaned_question:
            return

        with st.chat_message("user"):
            st.markdown(cleaned_question)

        with st.chat_message("assistant"):
            with st.spinner(
                "Searching the PDF and "
                "generating an answer..."
            ):
                result = ask_question(
                    chat_id=chat_id,
                    question=cleaned_question,
                )

            if result is not None:
                answer = result.get(
                    "answer",
                    "No answer was returned.",
                )

                st.markdown(answer)

        if result is not None:
            st.rerun()

# ── Main application ──────────────────────────────────────────────────────────

def run_app() -> None:
    if not st.session_state.access_token:
        render_authentication_screen()
        return

    if st.session_state.current_user is None:
        if not load_current_user():
            render_authentication_screen()
            return

    chats = render_sidebar()

    selected_chat_id = (
        st.session_state.selected_chat_id
    )

    if selected_chat_id:
        selected_chat = next(
            (
                chat
                for chat in chats
                if chat.get("chat_id")
                == selected_chat_id
            ),
            None,
        )

        if selected_chat is None:
            st.session_state.selected_chat_id = None
            st.session_state.selected_chat_name = None

            st.warning(
                "The selected chat could not be found."
            )

            render_welcome_screen()
            return

        selected_chat_name = (
            selected_chat.get("chat_name")
            or st.session_state.selected_chat_name
            or "Untitled chat"
        )

        st.session_state.selected_chat_name = (
            selected_chat_name
        )

        render_chat_screen(
            chat_id=selected_chat_id,
            chat_name=selected_chat_name,
        )

        return

    if st.session_state.new_chat_mode:
        render_new_chat_screen()
        return

    render_welcome_screen()


run_app()