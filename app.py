import streamlit as st
from Crypto.Cipher import AES
import base64
import cv2
import numpy as np
import time
from io import BytesIO

# --- CORE LOGIC (Preserved from your original script) ---

END_MARKER = "#####"

def message_to_binary(message):
    if type(message) == str:
        return ''.join([format(ord(i), '08b') for i in message])
    elif type(message) == bytes or type(message) == np.ndarray:
        return [format(i, '08b') for i in message]
    elif type(message) == int or type(message) == np.uint8:
        return format(message, '08b')
    else:
        raise TypeError("Input type not supported")

def encrypt_message(secret_message, key):
    aes_key = key.ljust(32)[:32].encode("utf-8")
    cipher = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(secret_message.encode("utf-8"))
    encrypted_data = cipher.nonce + tag + ciphertext
    return base64.b64encode(encrypted_data).decode("utf-8")

def decrypt_message(encrypted_message, key):
    aes_key = key.ljust(32)[:32].encode("utf-8")
    try:
        encrypted_data = base64.b64decode(encrypted_message.encode("utf-8"), validate=True)
        nonce = encrypted_data[:16]
        tag = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]
        cipher = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted_data.decode("utf-8")
    except Exception:
        return "Decryption failed (wrong key or corrupted data)"

def hide_message(image, secret_message, key):
    encrypted = encrypt_message(secret_message, key) + END_MARKER
    binary_secret_msg = message_to_binary(encrypted)
    
    # Validation
    n_bytes = image.shape[0] * image.shape[1] * 3 // 8
    if len(encrypted) > n_bytes:
        return None, "Error: Image too small for this message."

    data_index = 0
    stego_img = image.copy()
    
    for row in stego_img:
        for pixel in row:
            for i in range(3): # RGB channels
                if data_index < len(binary_secret_msg):
                    channel_bin = format(pixel[i], '08b')
                    pixel[i] = int(channel_bin[:-1] + binary_secret_msg[data_index], 2)
                    data_index += 1
            if data_index >= len(binary_secret_msg):
                return stego_img, None
    return stego_img, None

def decode_message_logic(image, key):
    binary_data = ""
    for row in image:
        for pixel in row:
            for i in range(3):
                channel_bin = format(pixel[i], '08b')
                binary_data += channel_bin[-1]
    
    # Extract until END_MARKER
    all_bytes = [binary_data[i:i + 8] for i in range(0, len(binary_data), 8)]
    decoded_raw = ""
    for byte in all_bytes:
        decoded_raw += chr(int(byte, 2))
        if decoded_raw.endswith(END_MARKER):
            encrypted_payload = decoded_raw[:-len(END_MARKER)]
            return decrypt_message(encrypted_payload, key)
    return "Error: No hidden message found."

def calculate_metrics(original, stego):
    mse = np.mean((original.astype("float64") - stego.astype("float64")) ** 2)
    psnr = 10 * np.log10((255.0 ** 2) / mse) if mse != 0 else float('inf')
    return mse, psnr

# --- STREAMLIT UI ---

st.set_page_config(page_title="CyberStegano Tool", layout="wide")

st.title("🔐 Secure Image Steganography")
st.markdown("---")

tab1, tab2 = st.tabs(["📤 Encode (Hide Message)", "📥 Decode (Extract Message)"])

# ENCODING TAB
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("1. Configuration")
        uploaded_file = st.file_uploader("Choose an Image", type=["png", "jpg", "jpeg"], key="enc_upload")
        secret_text = st.text_area("Secret Message", placeholder="Enter the message you want to hide...")
        enc_key = st.text_input("Encryption Key", type="password", placeholder="Keep this safe!")
        
    with col2:
        if uploaded_file and secret_text and enc_key:
            st.header("2. Preview & Action")
            # Read image
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Original Image", use_container_width=True)
            
            if st.button("🚀 Encode and Encrypt"):
                start_time = time.perf_counter()
                stego_img, err = hide_message(img, secret_text, enc_key)
                end_time = time.perf_counter()
                
                if err:
                    st.error(err)
                else:
                    duration = end_time - start_time
                    mse, psnr = calculate_metrics(img, stego_img)
                    
                    st.success(f"Encoding Complete in {duration:.4f}s!")
                    
                    # Metrics Display
                    m1, m2 = st.columns(2)
                    m1.metric("MSE", f"{mse:.4f}")
                    m2.metric("PSNR", f"{psnr:.2f} dB")
                    
                    # Download Button
                    _, result_img = cv2.imencode(".png", stego_img)
                    st.download_button(
                        label="💾 Download Stego-Image",
                        data=result_img.tobytes(),
                        file_name="stego_output.png",
                        mime="image/png"
                    )

# DECODING TAB
with tab2:
    col3, col4 = st.columns(2)
    
    with col3:
        st.header("1. Upload Stego-Image")
        stego_file = st.file_uploader("Upload the PNG with hidden data", type=["png"], key="dec_upload")
        dec_key = st.text_input("Decryption Key", type="password", key="dec_pass")
        
    with col4:
        if stego_file and dec_key:
            st.header("2. Extraction")
            file_bytes = np.asarray(bytearray(stego_file.read()), dtype=np.uint8)
            img_to_decode = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            st.image(cv2.cvtColor(img_to_decode, cv2.COLOR_BGR2RGB), caption="Stego Image", use_container_width=True)
            
            if st.button("🔓 Extract Message"):
                with st.spinner("Decrypting..."):
                    result = decode_message_logic(img_to_decode, dec_key)
                    st.subheader("Decoded Message:")
                    if "Error" in result or "failed" in result:
                        st.error(result)
                    else:
                        st.info(result)

st.markdown("---")
st.caption("Developed for Graduation Project - Cybersecurity Department")