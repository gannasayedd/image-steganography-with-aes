import cv2
import numpy as np
import streamlit as st
import time

import test


st.set_page_config(
    page_title="AES Steganography Studio",
    page_icon="🔐",
    layout="wide",
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


st.markdown(
    """
    <style>
      .stApp {
        background:
          radial-gradient(circle at top left, rgba(214, 114, 76, 0.20), transparent 28%),
          radial-gradient(circle at bottom right, rgba(31, 77, 91, 0.20), transparent 28%),
          linear-gradient(135deg, #f5eddb 0%, #f6f3eb 46%, #e0ece7 100%);
      }
      .hero {
        padding: 1.6rem 1.8rem;
        border: 1px solid rgba(17, 33, 45, 0.08);
        border-radius: 24px;
        background: rgba(255, 250, 242, 0.82);
        backdrop-filter: blur(10px);
        box-shadow: 0 18px 50px rgba(17, 33, 45, 0.10);
        margin-bottom: 1.2rem;
      }
      .hero h1 {
        margin: 0;
        color: #12202c;
        font-size: 3rem;
        line-height: 0.95;
      }
      .hero p {
        margin: 0.9rem 0 0;
        color: #2c4953;
        font-size: 1.02rem;
        line-height: 1.75;
        max-width: 58rem;
      }
      .note-card {
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: rgba(49, 82, 91, 0.08);
        border: 1px solid rgba(49, 82, 91, 0.12);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>AES + LSB Steganography Studio</h1>
      <p>
        This app encrypts a secret message with AES, hides it inside a PNG using Least Significant Bit steganography,
        and reports your evaluation metrics: MSE, PSNR, and processing time.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

info1, info2, info3 = st.columns(3)
info1.markdown('<div class="note-card"><strong>Cover format</strong><br>Use PNG only for safe hidden data storage.</div>', unsafe_allow_html=True)
info2.markdown('<div class="note-card"><strong>Security</strong><br>Use the same key for encryption and decryption.</div>', unsafe_allow_html=True)
info3.markdown('<div class="note-card"><strong>Evaluation</strong><br>Measure imperceptibility with PSNR and distortion with MSE.</div>', unsafe_allow_html=True)

encode_tab, decode_tab = st.tabs(["Encode", "Decode"])

with encode_tab:
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Hide a Secret Message")
        encode_file = st.file_uploader(
            "Upload a PNG cover image",
            type=["png"],
            key="encode_file",
        )
        secret_message = st.text_area(
            "Secret message",
            placeholder="Write the secret message here...",
            height=180,
        )
        encode_key = st.text_input(
            "Encryption key",
            type="password",
        )

        encode_clicked = st.button("Encrypt and Hide", type="primary", use_container_width=True)

    with right:
        st.subheader("Preview")
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

            st.success("Message encrypted and hidden successfully.")
            render_metric_cards(mse, psnr, processing_time)

            preview_left, preview_right = st.columns(2)
            preview_left.image(to_rgb(original_image), caption="Original image", use_container_width=True)
            preview_right.image(to_rgb(encoded_image), caption="Stego image", use_container_width=True)

            st.download_button(
                "Download Stego PNG",
                data=png_buffer.tobytes(),
                file_name="stego_output.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception as error:
            st.error(str(error))

with decode_tab:
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Extract a Hidden Message")
        decode_file = st.file_uploader(
            "Upload a PNG stego image",
            type=["png"],
            key="decode_file",
        )
        decode_key = st.text_input(
            "Decryption key",
            type="password",
            key="decode_key",
        )
        decode_clicked = st.button("Extract and Decrypt", type="primary", use_container_width=True)

    with right:
        st.subheader("Preview")
        if decode_file is not None:
            decode_preview = uploaded_png_to_cv2(decode_file)
            st.image(to_rgb(decode_preview), caption="Stego PNG image", use_container_width=True)
        else:
            st.info("Upload a PNG stego image to preview it here.")

    if decode_clicked:
        try:
            image = uploaded_png_to_cv2(decode_file)
            if not decode_key.strip():
                raise ValueError("Decryption key cannot be empty.")

            start_time = time.perf_counter()
            decoded_message = test.decode_message(image, decode_key.strip())
            processing_time = time.perf_counter() - start_time

            if decoded_message == "Decryption failed (wrong key or corrupted data)":
                st.error(decoded_message)
            else:
                st.success("Message extracted successfully.")
                st.text_area("Decoded message", decoded_message, height=180)
            st.metric("Processing Time", f"{processing_time:.6f} s")
        except Exception as error:
            st.error(str(error))
