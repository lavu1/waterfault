"""Dependency-free local HTTP server for the WaterFault prototype."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from waterfault import DomainError, WaterFaultStore


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE = PROJECT_ROOT / ".data" / "waterfault.db"
WEB_ROOT = PROJECT_ROOT / "web"


def build_handler(store: WaterFaultStore, web_root: Path = WEB_ROOT) -> type[BaseHTTPRequestHandler]:
    class WaterFaultHandler(BaseHTTPRequestHandler):
        server_version = "WaterFault/1.0"

        def _json_body(self) -> dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise DomainError("Invalid content length.") from error
            if length > 1_000_000:
                raise DomainError("Request body is too large.", 413)
            if length == 0:
                return {}
            try:
                payload = json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                raise DomainError("Request body must be valid JSON.") from error
            if not isinstance(payload, dict):
                raise DomainError("Request body must be a JSON object.")
            return payload

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def _send_static(self, request_path: str) -> None:
            relative = "index.html" if request_path == "/" else request_path.lstrip("/")
            target = (web_root / relative).resolve()
            root = web_root.resolve()
            if target != root and root not in target.parents:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            if not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content = target.read_bytes()
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") or content_type == "application/javascript" else content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self) -> None:
            request_path = urlparse(self.path).path
            if request_path == "/api/state":
                self._send_json(HTTPStatus.OK, store.get_state())
                return
            if request_path == "/health":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return
            self._send_static(request_path)

        def do_POST(self) -> None:
            request_path = urlparse(self.path).path
            try:
                payload = self._json_body()
                if request_path == "/api/reports":
                    self._send_json(HTTPStatus.CREATED, store.create_report(payload))
                    return

                match = re.fullmatch(r"/api/reports/(\d+)/link", request_path)
                if match:
                    issue_id = int(payload.get("issue_id", 0))
                    self._send_json(HTTPStatus.OK, store.link_report(int(match.group(1)), issue_id))
                    return

                match = re.fullmatch(r"/api/issues/(\d+)/assign", request_path)
                if match:
                    crew_id = int(payload.get("crew_id", 0))
                    self._send_json(HTTPStatus.CREATED, store.assign_crew(int(match.group(1)), crew_id))
                    return

                match = re.fullmatch(r"/api/issues/(\d+)/resolve", request_path)
                if match:
                    self._send_json(HTTPStatus.OK, store.resolve_issue(int(match.group(1))))
                    return

                if request_path == "/api/reset":
                    store.initialize(reset=True)
                    self._send_json(HTTPStatus.OK, {"reset": True})
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})
            except DomainError as error:
                self._send_json(error.status, {"error": str(error)})
            except (TypeError, ValueError):
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Expected a numeric identifier."})
            except Exception:
                self.log_error("Unexpected server error")
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "WaterFault could not complete that action."})

        def log_message(self, format: str, *args: Any) -> None:
            print(f"[waterfault] {self.address_string()} - {format % args}")

    return WaterFaultHandler


def create_server(
    host: str = "127.0.0.1",
    port: int = 5183,
    database_path: Path | str = DEFAULT_DATABASE,
    reset: bool = False,
) -> ThreadingHTTPServer:
    store = WaterFaultStore(database_path, PROJECT_ROOT)
    store.initialize(reset=reset)
    return ThreadingHTTPServer((host, port), build_handler(store))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the WaterFault local prototype.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5183)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--reset", action="store_true", help="Restore the synthetic demonstration data.")
    arguments = parser.parse_args()

    server = create_server(arguments.host, arguments.port, arguments.database, arguments.reset)
    print(f"WaterFault is running at http://{arguments.host}:{server.server_port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
