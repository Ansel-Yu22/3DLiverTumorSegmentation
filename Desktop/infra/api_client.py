import json
import os
import urllib.request


class ApiClient(object):
    def __init__(self, base_url=None):
        self.base_url = ""
        self.set_base_url(base_url)

    def set_base_url(self, base_url):
        value = (base_url or "").strip()
        if not value:
            value = "http://127.0.0.1:8000"
        self.base_url = value.rstrip("/")

    @staticmethod
    def decode_json_response(response):
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}

    @staticmethod
    def read_http_error(exc):
        try:
            detail = exc.read().decode("utf-8", errors="ignore").strip()
            return detail if detail else str(exc)
        except Exception:
            return str(exc)

    def request_json(self, method, path, payload=None, auth_header=None, timeout=30):
        url = f"{self.base_url}{path}"
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method)
        if payload is not None:
            req.add_header("Content-Type", "application/json")
        if auth_header:
            req.add_header("Authorization", auth_header)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return self.decode_json_response(resp)

    def submit_file_job(self, file_path, endpoint="/jobs", auth_header=None, timeout=120):
        boundary = f"----PyQtBoundary{os.urandom(12).hex()}"
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        payload = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(f"{self.base_url}{endpoint}", data=payload, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        req.add_header("Content-Length", str(len(payload)))
        if auth_header:
            req.add_header("Authorization", auth_header)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return self.decode_json_response(resp)

    def query_job(self, job_id, timeout=30):
        return self.request_json("GET", f"/jobs/{job_id}", timeout=timeout)
