"""A small webhook receiver that checks every delivery's signature.

Run it with AYINBOX_WEBHOOK_SECRET set to the endpoint secret (whsec_...), then
point a webhook endpoint at it through an HTTPS tunnel.
"""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from ayinbox import SignatureVerificationError, construct_event

SECRET = os.environ["AYINBOX_WEBHOOK_SECRET"]


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        try:
            event = construct_event(raw, self.headers.get("X-Ayinbox-Signature", ""), SECRET)
        except SignatureVerificationError:
            self.send_response(400)
            self.end_headers()
            return
        # X-Ayinbox-Event-Id is stable across retries: use it to drop duplicates.
        print(event.get("event_type"), self.headers.get("X-Ayinbox-Event-Id"))
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
