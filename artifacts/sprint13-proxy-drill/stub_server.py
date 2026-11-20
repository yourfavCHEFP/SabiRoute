"""Deterministic OpenAI-compatible stub for the proxy drill.

Modes via SABI_DRILL_MODE env: success | error500 | error401 | reset |
hang | delay12 | malformed. Counts every inbound POST to /v1/chat/completions
in memory and logs one line per request (no bodies, no headers).
Runs on python:3.12-slim, stdlib only.
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE = os.environ.get("SABI_DRILL_MODE", "success")
COUNT = 0


class Handler(BaseHTTPRequestHandler):
    server_version = "SabiDrillStub/1.0"

    def log_message(self, *args):
        pass

    def _count(self, note):
        global COUNT
        COUNT += 1
        print(f"stub_request n={COUNT} path={self.path} note={note}", flush=True)

    def do_POST(self):
        global COUNT
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)
        if self.path == "/v1/chat/completions":
            if MODE == "reset":
                self._count("reset")
                try:
                    self.connection.shutdown(2)
                except OSError:
                    pass
                self.connection.close()
                return
            if MODE == "hang":
                self._count("hang-accepted")
                time.sleep(60)
                return
            if MODE == "delay12":
                self._count("delay12")
                time.sleep(12)
            else:
                self._count(MODE)
            if MODE == "error500":
                body, status = {"error": {"message": "stub down", "type": "server_error"}}, 500
            elif MODE == "error401":
                body, status = {"error": {"message": "stub bad key", "type": "auth_error"}}, 401
            elif MODE == "malformed":
                raw = b"this is not json {{{"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            else:
                body, status = {
                    "id": "chatcmpl-drill",
                    "object": "chat.completion",
                    "model": "sabi-stub-model",
                    "choices": [{"message": {"role": "assistant", "content": "drill-ok"}}],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
                }, 200
            encoded = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8399), Handler).serve_forever()
