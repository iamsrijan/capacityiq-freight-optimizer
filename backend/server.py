from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from config import API_ENDPOINTS
from optimizer import optimise_corridor
from repository import DATASET, dataset_summary, find_corridor
from utils import apply_limit, as_float, as_int


class CapacityIQHandler(BaseHTTPRequestHandler):
    server_version = "CapacityIQLocalBackend/1.0"

    def _send_json(self, status: int, payload: Any) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        self._send_json(204, {})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if path in {"/", "/api", "/api/health"}:
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "CapacityIQ local backend",
                    "dataset": dataset_summary(),
                    "endpoints": API_ENDPOINTS,
                },
            )
            return

        if path == "/api/corridors":
            self._send_json(200, DATASET["corridors"])
            return

        if path.startswith("/api/corridors/"):
            corridor_id = unquote(path.removeprefix("/api/corridors/"))
            corridor = find_corridor(corridor_id)
            self._send_json(200, corridor) if corridor else self._send_json(
                404,
                {"error": f"Unknown corridor: {corridor_id}"},
            )
            return

        if path == "/api/shipments":
            corridor_id = query.get("corridor_id", [""])[0]
            shipments = [
                shipment
                for corridor in DATASET["corridors"]
                if not corridor_id or corridor["id"] == corridor_id
                for shipment in corridor["shipments"]
            ]
            self._send_json(200, {"count": len(shipments), "rows": apply_limit(shipments, query)})
            return

        if path == "/api/capacity":
            corridor_id = query.get("corridor_id", [""])[0]
            capacity = [
                mode
                for corridor in DATASET["corridors"]
                if not corridor_id or corridor["id"] == corridor_id
                for mode in corridor["modes"]
            ]
            self._send_json(200, {"count": len(capacity), "rows": apply_limit(capacity, query)})
            return

        if path == "/api/retail-profiles":
            self._send_json(200, DATASET["retailProfiles"])
            return

        if path == "/api/hubs":
            self._send_json(200, {"count": len(DATASET["hubs"]), "rows": apply_limit(DATASET["hubs"], query)})
            return

        if path == "/api/partners":
            self._send_json(200, {"count": len(DATASET["partners"]), "rows": apply_limit(DATASET["partners"], query)})
            return

        if path == "/api/tables":
            self._send_json(200, dataset_summary())
            return

        self._send_json(404, {"error": f"Unknown endpoint: {path}"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path not in {"/api/optimise", "/api/optimize"}:
            self._send_json(404, {"error": f"Unknown endpoint: {path}"})
            return

        length = as_int(self.headers.get("Content-Length"), 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Request body must be valid JSON"})
            return

        corridor_id = payload.get("corridorId") or payload.get("corridor_id") or "northeast"
        corridor = find_corridor(str(corridor_id))
        if not corridor:
            self._send_json(404, {"error": f"Unknown corridor: {corridor_id}"})
            return

        result = optimise_corridor(
            corridor,
            bool(payload.get("anchorEnabled", True)),
            as_float(payload.get("anchorMultiplier", 1), 1),
            as_int(payload.get("maxDetour", 120), 120),
            as_int(payload.get("guardrail", 74), 74),
        )
        self._send_json(200, {"corridor": corridor, "result": result})

    def log_message(self, format: str, *args: Any) -> None:
        if getattr(self.server, "quiet", False):
            return
        super().log_message(format, *args)


def run(host: str, port: int, quiet: bool = False) -> None:
    server = ThreadingHTTPServer((host, port), CapacityIQHandler)
    server.quiet = quiet  # type: ignore[attr-defined]
    print(f"CapacityIQ backend running at http://{host}:{port}")
    print(f"Loaded dataset: {json.dumps(dataset_summary(), indent=2)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCapacityIQ backend stopped")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CapacityIQ local backend API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    run(args.host, args.port, args.quiet)


if __name__ == "__main__":
    main()
