import base64
import json
import time
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np

import test


PROJECT_DIR = Path(__file__).resolve().parent
WEB_DIR = PROJECT_DIR / "web"
HOST = "127.0.0.1"
PORT = 8000


def parse_multipart(content_type: str, body: bytes) -> dict:
    header = (
        f"Content-Type: {content_type}\r\n"
        "MIME-Version: 1.0\r\n\r\n"
    ).encode("utf-8")
    message = BytesParser(policy=default).parsebytes(header + body)

    fields = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        payload = part.get_payload(decode=True)

        if filename:
            fields[name] = {
                "filename": filename,
                "content": payload,
                "content_type": part.get_content_type(),
            }
        else:
            fields[name] = payload.decode("utf-8").strip()

    return fields


def decode_uploaded_png(file_data: dict) -> np.ndarray:
    filename = file_data.get("filename", "")
    if Path(filename).suffix.lower() != ".png":
        raise ValueError("Please upload a PNG image only.")

    raw = np.frombuffer(file_data["content"], dtype=np.uint8)
    image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not read the uploaded image.")
    return image


class StegoWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.serve_index()
            return

        if parsed.path == "/health":
            self.send_json({"status": "ok"})
            return

        self.send_error(404, "Page not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        if "multipart/form-data" not in content_type:
            self.send_json({"error": "Form data is required."}, status=400)
            return

        try:
            fields = parse_multipart(content_type, body)
        except Exception:
            self.send_json({"error": "Could not read submitted form data."}, status=400)
            return

        try:
            if parsed.path == "/encode":
                self.handle_encode(fields)
                return
            if parsed.path == "/decode":
                self.handle_decode(fields)
                return
            self.send_error(404, "Page not found")
        except Exception as error:
            self.send_json({"error": str(error)}, status=400)

    def serve_index(self):
        index_path = WEB_DIR / "index.html"
        content = index_path.read_text(encoding="utf-8")
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_encode(self, fields: dict):
        if "image" not in fields:
            raise ValueError("Please choose a PNG cover image.")

        message = fields.get("message", "")
        key = fields.get("key", "")

        if not message:
            raise ValueError("Secret message is required.")
        if not key:
            raise ValueError("Encryption key is required.")

        image = decode_uploaded_png(fields["image"])
        original = image.copy()

        start_time = time.perf_counter()
        stego = test.hide_message(image.copy(), message, key)
        processing_time = time.perf_counter() - start_time

        mse = test.calculate_mse(original, stego)
        psnr = test.calculate_psnr(original, stego)

        ok, encoded_png = cv2.imencode(".png", stego)
        if not ok:
            raise ValueError("Could not create the encoded PNG.")

        payload = {
            "message": "Message encrypted and hidden successfully.",
            "metrics": {
                "mse": round(float(mse), 10),
                "psnr": "Infinity" if np.isinf(psnr) else round(float(psnr), 4),
                "processing_time": round(float(processing_time), 6),
            },
            "download_name": "stego_output.png",
            "image_base64": base64.b64encode(encoded_png.tobytes()).decode("utf-8"),
        }
        self.send_json(payload)

    def handle_decode(self, fields: dict):
        if "image" not in fields:
            raise ValueError("Please choose a PNG stego image.")

        key = fields.get("key", "")
        if not key:
            raise ValueError("Decryption key is required.")

        image = decode_uploaded_png(fields["image"])

        start_time = time.perf_counter()
        decoded_message = test.decode_message(image, key)
        processing_time = time.perf_counter() - start_time

        payload = {
            "message": decoded_message,
            "processing_time": round(float(processing_time), 6),
        }
        self.send_json(payload)

    def send_json(self, payload: dict, status: int = 200):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


def run_server():
    server = ThreadingHTTPServer((HOST, PORT), StegoWebHandler)
    print(f"Steganography website running on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
