from Crypto.Cipher import AES
import base64
import cv2
import numpy as np
from pathlib import Path
import time


END_MARKER = "#####"

# add comment line
# ===============================
# TEXT/BINARY
# ===============================

def message_to_binary(message):
    if type(message) == str:
        return ''.join([format(ord(i), '08b') for i in message])
    elif type(message) == bytes or type(message) == np.ndarray:
        return [format(i, '08b') for i in message]
    elif type(message) == int or type(message) == np.uint8:
        return format(message, '08b')
    else:
        raise TypeError("Input type not supported")

# ===============================
# AES Encryption
# ===============================

def encrypt_message(secret_message, key):
    if not key:
        raise ValueError("Error: Encryption key cannot be empty.")

    aes_key = key.ljust(32)[:32].encode("utf-8")
    cipher = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(secret_message.encode("utf-8"))
    encrypted_data = cipher.nonce + tag + ciphertext
    return base64.b64encode(encrypted_data).decode("utf-8")

# ===============================
# AES Decryption
# ===============================

def decrypt_message(encrypted_message, key):
    if not key:
        raise ValueError("Error: Decryption key cannot be empty.")

    aes_key = key.ljust(32)[:32].encode("utf-8")

    try:
        encrypted_data = base64.b64decode(encrypted_message.encode("utf-8"), validate=True)
        nonce = encrypted_data[:16]
        tag = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]

        if len(nonce) != 16 or len(tag) != 16 or len(ciphertext) == 0:
            raise ValueError

        cipher = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted_data.decode("utf-8")
    except Exception:
        return "Decryption failed (wrong key or corrupted data)"

# ===============================
# LSB EMBEDDING
# ===============================

def hide_message(image, secret_message, key):
    encrypted = encrypt_message(secret_message, key) + END_MARKER

    n_bytes = image.shape[0] * image.shape[1] * 3 // 8
    print("Maximum bytes to encode:", n_bytes)
    if len(encrypted) > n_bytes:
        raise ValueError("Error: Insufficient bytes, need bigger image or less data.")

    binary_secret_msg = message_to_binary(encrypted)
    data_index = 0

    for values in image:
        for pixel in values:
            r, g, b = message_to_binary(pixel)

            if data_index < len(binary_secret_msg):
                pixel[0] = int(r[:-1] + binary_secret_msg[data_index], 2)
                data_index += 1

            if data_index < len(binary_secret_msg):
                pixel[1] = int(g[:-1] + binary_secret_msg[data_index], 2)
                data_index += 1

            if data_index < len(binary_secret_msg):
                pixel[2] = int(b[:-1] + binary_secret_msg[data_index], 2)
                data_index += 1

            if data_index >= len(binary_secret_msg):
                return image

    return image

# ===============================
# EXTRACTION
# ===============================

def binary_to_message(binary_data):
    all_bytes = [binary_data[i:i + 8] for i in range(0, len(binary_data), 8)]
    decoded_message = ""

    for byte in all_bytes:
        decoded_message += chr(int(byte, 2))
        if decoded_message.endswith(END_MARKER):
            return decoded_message[:-len(END_MARKER)]

    raise ValueError("Error: No hidden message found in the image.")


def decode_message(image, key):
    binary_data = ""

    for values in image:
        for pixel in values:
            r, g, b = message_to_binary(pixel)
            binary_data += r[-1]
            binary_data += g[-1]
            binary_data += b[-1]

    encoded_message = binary_to_message(binary_data)
    return decrypt_message(encoded_message, key)


# ===============================
# EVALUATION METRICS
# ===============================

def validate_png_output(filename):
    if Path(filename).suffix.lower() != ".png":
        raise ValueError("Error: Output file must use the .png extension.")


def calculate_mse(original_image, stego_image):
    difference = original_image.astype("float64") - stego_image.astype("float64")
    return np.mean(difference ** 2)


def calculate_psnr(original_image, stego_image):
    mse = calculate_mse(original_image, stego_image)
    if mse == 0:
        return float("inf")
    max_pixel = 255.0
    return 10 * np.log10((max_pixel ** 2) / mse)


def print_evaluation_metrics(original_image, stego_image, processing_time):
    mse = calculate_mse(original_image, stego_image)
    psnr = calculate_psnr(original_image, stego_image)

    print("\nEvaluation Metrics")
    print("MSE:", mse)
    if psnr == float("inf"):
        print("PSNR: Infinity dB")
    else:
        print("PSNR:", psnr, "dB")
    print("Processing time:", processing_time, "seconds")

# ===============================
# ENCODING INTERFACE
# ===============================

def encode_data():
    image_path = input("Enter the path of the image: ").strip()
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError("Error: Could not open image.")

    print("Image shape:", image.shape)

    data = input("Enter the secret message to hide: ").strip()
    if len(data) == 0:
        raise ValueError("Error: Secret message cannot be empty.")

    filename = input("Enter the output filename (with extension, e.g., output.png): ").strip()
    validate_png_output(filename)

    key = input("Enter the encryption key: ").strip()
    if len(key) == 0:
        raise ValueError("Error: Encryption key cannot be empty.")

    original_image = image.copy()
    start_time = time.perf_counter()
    encoded_image = hide_message(image, data, key)
    end_time = time.perf_counter()

    cv2.imwrite(filename, encoded_image)
    print("Message encrypted and hidden successfully in:", filename)
    print_evaluation_metrics(original_image, encoded_image, end_time - start_time)

# ===============================
# DECODING INTERFACE
# ===============================
def decode_data():
    image_path = input("Enter the path of the image to decode: ").strip()
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError("Error: Could not open image.")

    key = input("Enter the decryption key: ").strip()

    start_time = time.perf_counter()
    decoded_message = decode_message(image, key)
    end_time = time.perf_counter()

    print("Decoded message:", decoded_message)
    print("Processing time:", end_time - start_time, "seconds")
    return decoded_message


def steganography():
    userinput = input(
        "Image Steganography\n"
        "1. Encode the data\n"
        "2. Decode the data\n"
        "Your input is: "
    ).strip()

    if userinput == "1":
        print("\nEncoding....")
        encode_data()
    elif userinput == "2":
        print("\nDecoding....")
        decode_data()
    else:
        raise ValueError("Enter correct input")


if __name__ == "__main__":
    try:
        steganography()
    except Exception as error:
        print(error)
