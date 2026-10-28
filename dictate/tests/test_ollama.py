from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer

from dictate.polish.ollama import OllamaPolisher


class UpperFallback:
    def __init__(self):
        self.calls = 0

    def polish(self, text: str) -> str:
        self.calls += 1
        return text.upper()


@contextmanager
def ollama_server(respond):
    """Spin up a local HTTP server; `respond(request_body) -> (status, body_dict|str, delay)`."""
    received: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            received.append({"path": self.path, "body": body})
            status, payload, delay = respond(body)
            if delay:
                time.sleep(delay)
            data = payload if isinstance(payload, str) else json.dumps(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data.encode())

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", received
    finally:
        server.shutdown()
        server.server_close()


def make_polisher(host, fallback=None, timeout=2.0):
    return OllamaPolisher(
        host=host,
        model="test-model",
        timeout_seconds=timeout,
        fallback=fallback or UpperFallback(),
    )


def test_returns_llm_response_stripped():
    with ollama_server(lambda b: (200, {"response": '  "The meeting is tomorrow." \n'}, 0)) as (
        host,
        _,
    ):
        polisher = make_polisher(host)
        assert polisher.polish("um the meeting is tomorrow") == "The meeting is tomorrow."


def test_sends_model_text_and_no_streaming():
    with ollama_server(lambda b: (200, {"response": "ok"}, 0)) as (host, received):
        make_polisher(host).polish("hello world")
    body = received[0]["body"]
    assert received[0]["path"] == "/api/generate"
    assert body["model"] == "test-model"
    assert body["stream"] is False
    assert "hello world" in body["prompt"]
    assert "filler" in body["system"].lower()


def test_timeout_falls_back_to_rules():
    fallback = UpperFallback()
    with ollama_server(lambda b: (200, {"response": "too late"}, 1.0)) as (host, _):
        polisher = make_polisher(host, fallback=fallback, timeout=0.2)
        assert polisher.polish("hi there") == "HI THERE"
    assert fallback.calls == 1


def test_non_200_falls_back():
    with ollama_server(lambda b: (500, {"error": "model not found"}, 0)) as (host, _):
        assert make_polisher(host).polish("hi") == "HI"


def test_garbage_json_falls_back():
    with ollama_server(lambda b: (200, "{not json", 0)) as (host, _):
        assert make_polisher(host).polish("hi") == "HI"


def test_empty_response_falls_back():
    with ollama_server(lambda b: (200, {"response": "   "}, 0)) as (host, _):
        assert make_polisher(host).polish("hi") == "HI"


def test_preamble_response_falls_back():
    with ollama_server(
        lambda b: (200, {"response": "Sure! Here is the corrected text: Hi."}, 0)
    ) as (host, _):
        assert make_polisher(host).polish("hi") == "HI"


def test_wildly_long_response_falls_back():
    with ollama_server(lambda b: (200, {"response": "word " * 100}, 0)) as (host, _):
        assert make_polisher(host).polish("hi") == "HI"


def test_connection_refused_falls_back():
    polisher = make_polisher("http://127.0.0.1:1", timeout=0.5)
    assert polisher.polish("hi") == "HI"


def test_empty_input_short_circuits():
    polisher = make_polisher("http://127.0.0.1:1")
    assert polisher.polish("   ") == ""
