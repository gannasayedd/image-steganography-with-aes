import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import streamlit as st

import test


PAGES = ["Home", "Encode", "Decode", "Activity Logs", "Metrics Dashboard"]
LOGO_PATH = Path("stegoshield.png")

# Change these two values only.
APP_USERNAME = "admin"
APP_PASSWORD = "#Aou12"


st.set_page_config(
    page_title="StegoShield🛡️",
    layout="wide",
)


def init_session_state():
    defaults = {
        "current_page": "Home",
        "activity_logs": [],
        "wrong_password_attempts": 0,
        "metrics_history": [],
        "authenticated": False,
        "login_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_log(action, status, details):
    st.session_state.activity_logs.append(
        {
            "Time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "Action": action,
            "Status": status,
            "Details": details,
        }
    )


def uploaded_png_to_cv2(uploaded_file):
    if uploaded_file is None:
        raise ValueError("Please upload a PNG image.")
    if not uploaded_file.name.lower().endswith(".png"):
        raise ValueError("Only PNG images are allowed.")

    file_bytes = np.frombuffer(uploaded_file.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not read the uploaded image.")
    return image


def to_rgb(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def render_metric_cards(mse, psnr, processing_time):
    col1, col2, col3 = st.columns(3)
    col1.metric("MSE", f"{mse:.10f}")
    col2.metric("PSNR", "Infinity dB" if np.isinf(psnr) else f"{psnr:.4f} dB")
    col3.metric("Processing Time", f"{processing_time:.6f} s")


def metrics_dataframe():
    if not st.session_state.metrics_history:
        return pd.DataFrame(columns=["Run", "MSE", "PSNR", "Processing Time"])
    return pd.DataFrame(st.session_state.metrics_history)


def render_styles():
    st.markdown(
        """
        <style>
          :root {
            --ink: #143254;
            --muted: #4a6d95;
            --baby-blue: #e8f4ff;
            --sky-blue: #cdeeff;
            --navy-blue: #163d6b;
            --panel: rgba(255, 255, 255, 0.74);
            --line: rgba(55, 108, 176, 0.18);
            --shadow: 0 24px 70px rgba(37, 86, 148, 0.15);
          }

          .stApp {
            background:
              radial-gradient(circle at top left, rgba(117, 199, 255, 0.30), transparent 30%),
              radial-gradient(circle at top right, rgba(22, 61, 107, 0.20), transparent 50%),
              linear-gradient(135deg, var(--baby-blue) 0%, #f8fcff 38%, var(--sky-blue) 50%);
          }

          header[data-testid="stHeader"],
          div[data-testid="stToolbar"] {
            display: none;
          }

          #MainMenu,
          footer {
            visibility: hidden;
          }

          .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
          }

          .hero,
          .glass-card {
            padding: 1.5rem 1.7rem;
            border-radius: 26px;
            background: var(--panel);
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
            backdrop-filter: blur(12px);
          }

          .hero-title {
            margin: 0;
            color: var(--ink);
            font-size: 3.2rem;
            line-height: 0.92;
          }

          .hero-text {
            margin: 0.85rem 0 0;
            color: var(--muted);
            max-width: 58rem;
            line-height: 1.8;
            font-size: 1.02rem;
          }

          .mini-card {
            padding: 1rem 1.1rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.68);
            border: 1px solid rgba(55, 108, 176, 0.14);
            min-height: 116px;
          }

          .mini-card strong {
            display: block;
            margin-bottom: 0.35rem;
            color: var(--navy-blue);
          }

          .nav-shell {
            padding: 0.95rem 1.1rem 0.8rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.62);
            border: 1px solid rgba(55, 108, 176, 0.14);
            box-shadow: 0 18px 44px rgba(37, 86, 148, 0.10);
            backdrop-filter: blur(10px);
            margin-bottom: 0.9rem;
          }

          .top-nav-note {
            color: var(--muted);
            font-size: 0.9rem;
            margin-bottom: 0.55rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
          }

          div.stButton > button {
            border-radius: 999px;
            border: 1px solid rgba(96, 118, 143, 0.22);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(219, 228, 238, 0.94) 100%);
            color: #24384d;
            font-weight: 700;
            letter-spacing: 0.01em;
            min-height: 2.9rem;
            padding: 0.5rem 1.15rem;
            box-shadow:
              inset 0 1px 0 rgba(255, 255, 255, 0.85),
              0 10px 24px rgba(110, 120, 134, 0.14);
            transition: all 0.18s ease;
          }

          div.stButton > button:hover {
            border-color: rgba(79, 108, 141, 0.34);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(210, 221, 234, 0.95) 100%);
            color: #1b2f44;
            transform: translateY(-1px);
            box-shadow:
              inset 0 1px 0 rgba(255, 255, 255, 0.9),
              0 14px 28px rgba(84, 109, 138, 0.18);
          }

          div.stButton > button[kind="primary"] {
            background: linear-gradient(180deg, #f7fbff 0%, #cfdbea 100%);
            color: #15314f;
            border-color: rgba(63, 98, 138, 0.30);
            box-shadow:
              inset 0 1px 0 rgba(255, 255, 255, 0.95),
              0 12px 28px rgba(65, 102, 145, 0.18);
          }

          .login-card {
            max-width: 460px;
            margin: 7vh auto 0;
            padding: 2rem;
            border-radius: 26px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(55, 108, 176, 0.18);
            box-shadow: 0 24px 70px rgba(37, 86, 148, 0.15);
            backdrop-filter: blur(12px);
            text-align: center;
          }

          .login-title {
            margin: 0;
            color: var(--ink);
            font-size: 2.4rem;
            line-height: 1;
          }

          .login-subtitle {
            margin-top: 0.7rem;
            color: var(--muted);
            line-height: 1.7;
            
          }
        </style>
        """,
        unsafe_allow_html=True,
    )



def render_login_page():
    st.markdown(
        """
        <div class="login-card">
          <h1 class="login-title">StegoShield🛡️</h1>
          <p class="login-subtitle">
            Login first to access the image steganography system.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_clicked = st.form_submit_button("Login", use_container_width=True, type="primary")

    if login_clicked:
        if username == APP_USERNAME and password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.session_state.login_error = ""
            add_log("Login", "Success", "User logged in successfully.")
            st.rerun()
        else:
            st.session_state.login_error = "Invalid username or password."
            add_log("Login", "Failed", "Invalid login attempt.")

    if st.session_state.login_error:
        st.error(st.session_state.login_error)

def render_top_menu():
    cols = st.columns(len(PAGES) + 1)

    for i, page in enumerate(PAGES):
        button_type = "primary" if st.session_state.current_page == page else "secondary"
        if cols[i].button(page, key=f"nav_{page}", type=button_type, use_container_width=True):
            st.session_state.current_page = page
            st.rerun()

    if cols[-1].button("Logout", key="logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_page = "Home"
        add_log("Logout", "Success", "User logged out successfully.")
        st.rerun()


def render_home_page():
    hero_left, hero_right = st.columns([1.1, 0.4], vertical_alignment="center")
    with hero_left:
        st.markdown(
            """
            <div class="hero">
              <h1 class="hero-title">StegoShield🛡️</h1>
              <p class="hero-text">
                A professional image steganography project that encrypts secret messages with AES before
                hiding them inside PNG images using Least Significant Bit embedding. The platform also tracks
                wrong password attempts, stores activity logs, compares original and stego images, and
                evaluates image quality using MSE and PSNR.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_right:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.info("Put `stegoshield.png` in the project folder to show the logo.")

    st.write("")
    card1, card2, card3 = st.columns(3)
    card1.markdown(
        '<div class="mini-card"><strong>About</strong>StegoShield🛡️: AES + LSB Image Steganography</div>',
        unsafe_allow_html=True,
    )
    card2.markdown(
        '<div class="mini-card"><strong>Description</strong>Hide encrypted messages in PNG images and measure imperceptibility and distortion.</div>',
        unsafe_allow_html=True,
    )
    card3.markdown(
        f'<div class="mini-card"><strong>Wrong Password Attempts</strong>{st.session_state.wrong_password_attempts}</div>',
        unsafe_allow_html=True,
    )

    st.write("")
    col1, col2 = st.columns(2)
    if col1.button("Encode", key="home_encode", use_container_width=True, type="primary"):
        st.session_state.current_page = "Encode"
        st.rerun()
    if col2.button("Decode", key="home_decode", use_container_width=True):
        st.session_state.current_page = "Decode"
        st.rerun()

    st.write("")
    st.markdown(
        """
        <div class="glass-card">
          <strong style="color:#163d6b;">Project Overview</strong>
          <p style="margin:0.7rem 0 0;color:#4a6d95;line-height:1.75;">
            Use the Encode page to protect and hide a message. Use the Decode page to recover it.
            The Activity Logs page records important events, and the Metrics Dashboard visualizes
            PSNR, MSE, and processing time from your encoding runs.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_encode_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Encode")
    st.write("Encrypt a secret message with AES and hide it inside a PNG image.")
    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        encode_file = st.file_uploader("Upload a PNG cover image", type=["png"], key="encode_file")
        secret_message = st.text_area(
            "Secret message",
            placeholder="Write the message to hide...",
            height=180,
        )
        encode_key = st.text_input("Encryption key", type="password", key="encode_key")
        encode_clicked = st.button("Encrypt and Hide", key="encode_submit", type="primary", use_container_width=True)

    with right:
        st.subheader("Cover Image Preview")
        if encode_file is not None:
            preview_image = uploaded_png_to_cv2(encode_file)
            st.image(to_rgb(preview_image), caption="Original PNG image", use_container_width=True)
        else:
            st.info("Upload a PNG image to preview it here.")

    if encode_clicked:
        try:
            image = uploaded_png_to_cv2(encode_file)
            if not secret_message.strip():
                raise ValueError("Secret message cannot be empty.")
            if not encode_key.strip():
                raise ValueError("Encryption key cannot be empty.")

            original_image = image.copy()
            start_time = time.perf_counter()
            encoded_image = test.hide_message(image.copy(), secret_message.strip(), encode_key.strip())
            processing_time = time.perf_counter() - start_time

            mse = test.calculate_mse(original_image, encoded_image)
            psnr = test.calculate_psnr(original_image, encoded_image)

            ok, png_buffer = cv2.imencode(".png", encoded_image)
            if not ok:
                raise ValueError("Could not generate the encoded PNG.")

            st.session_state.metrics_history.append(
                {
                    "Run": len(st.session_state.metrics_history) + 1,
                    "MSE": float(mse),
                    "PSNR": None if np.isinf(psnr) else float(psnr),
                    "Processing Time": float(processing_time),
                }
            )
            add_log("Encode", "Success", "Message encrypted and hidden successfully.")

            st.success("Message encrypted and hidden successfully.")
            render_metric_cards(mse, psnr, processing_time)

            st.subheader("Compare Original vs Stego Image")
            compare_left, compare_right = st.columns(2)
            compare_left.image(to_rgb(original_image), caption="Original Image", use_container_width=True)
            compare_right.image(to_rgb(encoded_image), caption="Stego Image", use_container_width=True)

            st.download_button(
                "Download Stego PNG",
                data=png_buffer.tobytes(),
                file_name="stego_output.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception as error:
            add_log("Encode", "Failed", str(error))
            st.error(str(error))


def render_decode_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Decode")
    st.write("Extract the hidden payload from a PNG image and decrypt it with the correct key.")
    st.markdown("</div>", unsafe_allow_html=True)

    stat1, stat2 = st.columns(2)
    stat1.metric("Wrong Password Attempt Counter", st.session_state.wrong_password_attempts)
    stat2.metric("Activity Log Entries", len(st.session_state.activity_logs))

    left, right = st.columns([1, 1])
    with left:
        decode_file = st.file_uploader("Upload a PNG stego image", type=["png"], key="decode_file")
        decode_key = st.text_input("Decryption key", type="password", key="decode_key")
        decode_clicked = st.button("Extract and Decrypt", key="decode_submit", type="primary", use_container_width=True)

    with right:
        st.subheader("Stego Image Preview")
        if decode_file is not None:
            decode_preview = uploaded_png_to_cv2(decode_file)
            st.image(to_rgb(decode_preview), caption="Stego PNG image", use_container_width=True)
        else:
            st.info("Upload a PNG image to preview it here.")

    if decode_clicked:
        try:
            image = uploaded_png_to_cv2(decode_file)
            if not decode_key.strip():
                raise ValueError("Decryption key cannot be empty.")

            start_time = time.perf_counter()
            decoded_message = test.decode_message(image, decode_key.strip())
            processing_time = time.perf_counter() - start_time

            if decoded_message == "Decryption failed (wrong key or corrupted data)":
                st.session_state.wrong_password_attempts += 1
                add_log("Decode", "Failed", "Wrong password or corrupted data.")
                st.error(decoded_message)
            else:
                add_log("Decode", "Success", "Message extracted successfully.")
                st.success("Message extracted successfully.")
                st.text_area("Decoded message", decoded_message, height=180)

            st.metric("Processing Time", f"{processing_time:.6f} s")
        except Exception as error:
            add_log("Decode", "Failed", str(error))
            st.error(str(error))


def render_logs_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Activity Logs")
    st.write("A running history of encode, decode, and error events.")
    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.activity_logs:
        st.info("No activity logs yet.")
        return

    logs_df = pd.DataFrame(st.session_state.activity_logs)
    st.dataframe(logs_df.iloc[::-1], use_container_width=True, hide_index=True)


def render_metrics_dashboard():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Metrics Dashboard")
    st.write("Graphs of PSNR, MSE, and processing time from your encoding runs.")
    st.markdown("</div>", unsafe_allow_html=True)

    metrics_df = metrics_dataframe()
    if metrics_df.empty:
        st.info("No metrics available yet. Run an encode operation first.")
        return

    st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    chart_df = metrics_df.set_index("Run")

    st.subheader("MSE Graph")
    st.line_chart(chart_df[["MSE"]], use_container_width=True)

    st.subheader("PSNR Graph")
    st.line_chart(chart_df[["PSNR"]], use_container_width=True)

    st.subheader("Processing Time Graph")
    st.line_chart(chart_df[["Processing Time"]], use_container_width=True)


def main():
    init_session_state()
    render_styles()

    if not st.session_state.authenticated:
        render_login_page()
        return

    render_top_menu()
    st.write("")

    if st.session_state.current_page == "Home":
        render_home_page()
    elif st.session_state.current_page == "Encode":
        render_encode_page()
    elif st.session_state.current_page == "Decode":
        render_decode_page()
    elif st.session_state.current_page == "Activity Logs":
        render_logs_page()
    elif st.session_state.current_page == "Metrics Dashboard":
        render_metrics_dashboard()


if __name__ == "__main__":
    main()
