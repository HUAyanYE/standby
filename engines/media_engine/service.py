"""媒体上传服务 — MinIO 对象存储 (无 boto3 依赖)

使用 MinIO S3 REST API 直接上传。
"""

import os
import uuid
import hmac
import hashlib
import datetime
import logging
import cgi
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json

logger = logging.getLogger(__name__)

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "standby")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "standby_dev_password")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "media")
PORT = int(os.environ.get("MEDIA_PORT", "8097"))


def s3_put_object(key, data, content_type="application/octet-stream"):
    """Upload object to S3-compatible storage using presigned URL approach."""
    # Use MinIO's anonymous put-object with pre-created bucket
    # For simplicity, use the MinIO console API
    import base64
    import hashlib
    import hmac

    now = datetime.datetime.utcnow()
    date_stamp = now.strftime("%Y%m%d")
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")

    # Simple PUT to S3
    url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{key}"
    
    # Create request
    req = Request(url, data=data, method="PUT")
    req.add_header("Content-Type", content_type)
    req.add_header("Content-Length", str(len(data)))
    
    # S3 auth (simplified for MinIO with path-style)
    # For MinIO with default credentials, we can use a simpler approach
    # Sign the request using AWS Signature V4
    
    service = "s3"
    region = "us-east-1"
    host = urlparse(MINIO_ENDPOINT).netloc
    
    # Canonical request
    canonical_uri = f"/{MINIO_BUCKET}/{key}"
    canonical_querystring = ""
    payload_hash = hashlib.sha256(data).hexdigest()
    
    headers_to_sign = {
        "content-type": content_type,
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    
    signed_headers = ";".join(sorted(headers_to_sign.keys()))
    canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted(headers_to_sign.items()))
    
    canonical_request = f"PUT\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    
    def sign(key, msg):
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()
    
    k_date = sign(f"AWS4{MINIO_SECRET_KEY}".encode(), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, "aws4_request")
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    
    auth = f"AWS4-HMAC-SHA256 Credential={MINIO_ACCESS_KEY}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    
    req.add_header("Authorization", auth)
    req.add_header("x-amz-content-sha256", payload_hash)
    req.add_header("x-amz-date", amz_date)
    req.add_header("x-amz-acl", "public-read")
    
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.status == 200
    except (URLError, HTTPError) as e:
        logger.error(f"S3 upload error: {e}")
        raise


def ensure_bucket():
    """Create bucket if it doesn't exist."""
    try:
        now = datetime.datetime.utcnow()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        host = urlparse(MINIO_ENDPOINT).netloc
        payload_hash = hashlib.sha256(b"").hexdigest()
        
        url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}"
        req = Request(url, method="PUT")
        
        service = "s3"
        region = "us-east-1"
        canonical_uri = f"/{MINIO_BUCKET}"
        canonical_querystring = ""
        headers_to_sign = {
            "host": host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        signed_headers = ";".join(sorted(headers_to_sign.keys()))
        canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted(headers_to_sign.items()))
        canonical_request = f"PUT\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        
        def sign(key, msg):
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()
        
        k_date = sign(f"AWS4{MINIO_SECRET_KEY}".encode(), date_stamp)
        k_region = sign(k_date, region)
        k_service = sign(k_region, service)
        k_signing = sign(k_service, "aws4_request")
        signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
        
        auth = f"AWS4-HMAC-SHA256 Credential={MINIO_ACCESS_KEY}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
        req.add_header("Authorization", auth)
        req.add_header("x-amz-content-sha256", payload_hash)
        req.add_header("x-amz-date", amz_date)
        
        urlopen(req, timeout=10)
        logger.info(f"Bucket {MINIO_BUCKET} ready")
    except HTTPError as e:
        if e.code == 409:
            logger.info(f"Bucket {MINIO_BUCKET} already exists")
        else:
            logger.warning(f"Bucket check: {e}")
    except Exception as e:
        logger.warning(f"Bucket check failed: {e}")


class MediaHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/upload":
            self.send_error(404)
            return

        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))

        if content_length == 0:
            self.send_json(400, {"error": "No file uploaded"})
            return

        body = self.rfile.read(content_length)

        file_data = None
        filename = "upload"
        mime = "application/octet-stream"
        media_type = "image"

        if "multipart/form-data" in content_type:
            try:
                # Extract boundary
                boundary = None
                for part in content_type.split(";"):
                    part = part.strip()
                    if part.startswith("boundary="):
                        boundary = part.split("=", 1)[1].strip('"')
                        break

                if not boundary:
                    self.send_json(400, {"error": "No boundary found"})
                    return

                boundary_bytes = boundary.encode()
                # Split body by boundary
                parts = body.split(b"--" + boundary_bytes)

                for part in parts:
                    if len(part) < 10:
                        continue
                    # Skip the closing boundary
                    if part.strip() == b"--" or part.strip() == b"":
                        continue

                    # Find header/body separator
                    sep = b"\r\n\r\n"
                    sep_idx = part.find(sep)
                    if sep_idx == -1:
                        continue

                    header_bytes = part[:sep_idx]
                    body_bytes = part[sep_idx + 4:]
                    # Remove trailing \r\n
                    if body_bytes.endswith(b"\r\n"):
                        body_bytes = body_bytes[:-2]

                    header_text = header_bytes.decode(errors="replace")

                    if 'name="file"' in header_text:
                        file_data = body_bytes
                        # Extract filename
                        if 'filename="' in header_text:
                            fn_start = header_text.index('filename="') + 10
                            fn_end = header_text.index('"', fn_start)
                            filename = header_text[fn_start:fn_end]
                        # Extract content-type
                        for line in header_text.split("\r\n"):
                            if line.lower().startswith("content-type:"):
                                mime = line.split(":", 1)[1].strip()
                    elif 'name="media_type"' in header_text:
                        media_type = body_bytes.decode(errors="replace").strip()

            except Exception as e:
                logger.error(f"Multipart parse error: {e}")
                self.send_json(400, {"error": f"Parse error: {e}"})
                return
        else:
            file_data = body
            mime = content_type

        if file_data is None or len(file_data) == 0:
            self.send_json(400, {"error": "No file field found"})
            return

            for part in parts:
                if b"Content-Disposition" in part:
                    headers_end = part.find(b"\r\n\r\n")
                    if headers_end == -1:
                        continue
                    part_headers = part[:headers_end].decode(errors="replace")
                    part_body = part[headers_end + 4:]
                    if part_body.endswith(b"\r\n"):
                        part_body = part_body[:-2]

                    if 'name="file"' in part_headers:
                        file_data = part_body
                        if 'filename="' in part_headers:
                            fn_start = part_headers.index('filename="') + 10
                            fn_end = part_headers.index('"', fn_start)
                            filename = part_headers[fn_start:fn_end]
                    elif 'name="media_type"' in part_headers:
                        media_type = part_body.decode(errors="replace").strip()

            if file_data is None:
                self.send_json(400, {"error": "No file field found"})
                return
        else:
            file_data = body
            filename = "upload"
            mime = content_type
            media_type = "image"

        ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        media_id = f"m_{uuid.uuid4().hex[:12]}"
        object_key = f"{media_id}.{ext}"

        try:
            s3_put_object(object_key, file_data, mime)
            logger.info(f"Uploaded {object_key} ({len(file_data)} bytes)")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            self.send_json(500, {"error": f"Upload failed: {e}"})
            return

        url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{object_key}"
        self.send_json(200, {
            "media_id": media_id,
            "url": url,
            "filename": filename,
            "size": len(file_data),
            "media_type": media_type,
        })

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        self.send_error(404)

    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logger.info(f"[media] {format % args}")


def main():
    logging.basicConfig(level=logging.INFO)
    ensure_bucket()
    server = HTTPServer(("0.0.0.0", PORT), MediaHandler)
    logger.info(f"Media service running on port {PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
