import secrets

from PIL import Image
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

HEADER_SIZE = 32  # 4 bytes to store encrypted payload length
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 32 bytes = AES-256
PBKDF2_ITERATIONS = 200_000


def bytes_to_binary(data: bytes) -> str:
    return "".join(format(byte, "08b") for byte in data)


def binary_to_bytes(binary_data: str) -> bytes:
    return bytes(
        int(binary_data[i:i + 8], 2)
        for i in range(0, len(binary_data), 8)
    )


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_message(message: str, password: str) -> bytes:
    salt = secrets.token_bytes(SALT_SIZE)
    nonce = secrets.token_bytes(NONCE_SIZE)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, message.encode("utf-8"), None)
    return salt + nonce + ciphertext


def decrypt_message(encrypted_payload: bytes, password: str) -> str:
    salt = encrypted_payload[:SALT_SIZE]
    nonce = encrypted_payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = encrypted_payload[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def get_capacity_bits(image: Image.Image) -> int:
    width, height = image.size
    return width * height * 3


def hide_payload(image: Image.Image, payload: bytes) -> Image.Image:
    payload_length = len(payload)
    header = payload_length.to_bytes(4, byteorder="big")
    full_payload = header + payload
    binary_payload = bytes_to_binary(full_payload)

    if len(binary_payload) > get_capacity_bits(image):
        raise ValueError("Error: Insufficient image capacity for encrypted data.")

    pixels = image.load()
    width, height = image.size
    data_index = 0

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            channels = [r, g, b]

            for channel in range(3):
                if data_index < len(binary_payload):
                    channels[channel] = (channels[channel] & 254) | int(binary_payload[data_index])
                    data_index += 1

            pixels[x, y] = tuple(channels)

            if data_index >= len(binary_payload):
                return image

    return image


def extract_payload(image: Image.Image) -> bytes:
    pixels = image.load()
    width, height = image.size
    bits = []

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits.append(str(r & 1))
            bits.append(str(g & 1))
            bits.append(str(b & 1))

    binary_string = "".join(bits)
    payload_length = int(binary_string[:HEADER_SIZE], 2)
    payload_bits = binary_string[HEADER_SIZE:HEADER_SIZE + (payload_length * 8)]

    if len(payload_bits) < payload_length * 8:
        raise ValueError("Error: Could not extract the full encrypted payload.")

    return binary_to_bytes(payload_bits)


def encode_message_in_image(image_path: str, secret_message: str, password: str, output_path: str) -> None:
    try:
        image = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        raise FileNotFoundError("Error: Could not open image.")

    encrypted_payload = encrypt_message(secret_message, password)
    stego_image = hide_payload(image.copy(), encrypted_payload)
    stego_image.save(output_path)
    print("Image size:", image.size)
    print("Maximum bits available:", get_capacity_bits(image))
    print("Encrypted message hidden successfully in:", output_path)


def decode_message_from_image(image_path: str, password: str) -> str:
    try:
        image = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        raise FileNotFoundError("Error: Could not open image.")

    encrypted_payload = extract_payload(image)
    return decrypt_message(encrypted_payload, password)


def encode_data() -> None:
    image_path = input("Enter the path of the image: ").strip()
    secret_message = input("Enter the secret message to hide: ").strip()
    password = input("Enter the AES password: ").strip()
    output_path = input("Enter the output filename (for example: output.png): ").strip()

    if not secret_message:
        raise ValueError("Error: Secret message cannot be empty.")
    if not password:
        raise ValueError("Error: Password cannot be empty.")

    encode_message_in_image(image_path, secret_message, password, output_path)


def decode_data() -> None:
    image_path = input("Enter the path of the image to decode: ").strip()
    password = input("Enter the AES password: ").strip()

    if not password:
        raise ValueError("Error: Password cannot be empty.")

    decoded_message = decode_message_from_image(image_path, password)
    print("Decoded message:", decoded_message)


def steganography() -> None:
    choice = input(
        "Image Steganography with AES-256\n"
        "1. Encode the data\n"
        "2. Decode the data\n"
        "Your input is: "
    ).strip()

    if choice == "1":
        print("\nEncoding...")
        encode_data()
    elif choice == "2":
        print("\nDecoding...")
        decode_data()
    else:
        raise ValueError("Enter 1 or 2 only.")


if __name__ == "__main__":
    steganography()
