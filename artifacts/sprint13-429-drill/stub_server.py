"""429 drill stub: scripted OpenAI-compatible responses with timed logs.

Modes via SABI_DRILL_MODE: success | error429 | error500 (control).
429 responses carry a Retry-After: 2 header like real rate limiters.
Counts inbound POSTs; logs arrivals/completions (use `docker logs -t`).
Stdlib only; no credentials; internal-network use.
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE = os.environ.get("SABI_DRILL_MODE", "success")
COUNT = 0


class Handler(BaseHTTPRequestHandler):
    server_version = "Sabi429Stub/1.0"

    def log_message(self, *args):
        pass

    def do_POST(self):
        global COUNT
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return
        COUNT += 1
        n = COUNT
        print(f"stub_request n={n} mode={MODE}", flush=True)
        t0 = time.monotonic()
        if MODE == "error429":
            body, status, extra = (
                {"error": {"message": "stub rate limited", "type": "rate_limit_error"}},
                429,
                {"Retry-After": "2"},
            )
        elif MODE == "error500":
            body, status, extra = (
                {"error": {"message": "stub down", "type": "server_error"}},
                500,
                {},
            )
        else:
            body, status, extra = (
                {
                    "id": "chatcmpl-429drill",
                    "object": "chat.completion",
                    "model": "sabi-429-model",
                    "choices": [{"message": {"role": "assistant", "content": "drill-ok"}}],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
                },
                200,
                {},
            )
        encoded = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        for k, v in extra.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(encoded)
        print(f"stub_done n={n} dt={time.monotonic()-t0:.2f}s", flush=True)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8399), Handler).serve_forever()
