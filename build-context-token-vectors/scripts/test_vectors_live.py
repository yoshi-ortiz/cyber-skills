#!/usr/bin/env python3
"""The served dashboard is a live tuning companion, not a static snapshot."""

from __future__ import annotations

import json
import sys
import threading
import types
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# The server boundary is standard-library-only. Stub the expensive analysis
# dependencies so this regression test stays a tight feedback loop.
sys.modules.setdefault("numpy", types.SimpleNamespace(ndarray=object))
sys.modules.setdefault("evoc", types.SimpleNamespace(EVoC=object))
sys.modules.setdefault("model2vec", types.SimpleNamespace(StaticModel=object))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vectors


def test() -> None:
    initial = {
        "skills": [], "root": "/skills", "model": "fixture", "seed": 42,
        "railOrder": [], "params": {}, "persistence": [],
        "layerStats": [{"clusters": 0, "noise": 0}],
    }
    calls: list[dict] = []

    def retune(params: dict) -> dict:
        calls.append(params)
        return {**initial, "params": params}

    server, url = vectors.companion(initial, retune, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(url, timeout=2) as response:
            html = response.read().decode("utf-8")
        assert 'id="tune"' in html, "served dashboard has no tuning controls"

        request = Request(
            url + "tune",
            data=json.dumps({"noise_level": 0.2, "n_neighbors": 10}).encode(),
            headers={"Content-Type": "application/json", "Origin": url.rstrip("/")},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            tuned = json.load(response)
        assert calls == [{"noise_level": 0.2, "n_neighbors": 10}]
        assert tuned["params"] == calls[0]
        with urlopen(url, timeout=2) as response:
            refreshed = response.read().decode("utf-8")
        assert '"noise_level": 0.2' in refreshed, "refresh lost the live session state"

        bad = Request(
            url + "tune", data=b'{"seed":99}',
            headers={"Content-Type": "application/json", "Origin": url.rstrip("/")},
            method="POST",
        )
        try:
            urlopen(bad, timeout=2)
        except HTTPError as response:
            assert response.code == 400
            assert "unknown parameter" in json.load(response)["error"]
        else:
            raise AssertionError("an undeclared tuning parameter was accepted")
        assert len(calls) == 1, "invalid input reached the analysis seam"

        cross_origin = Request(
            url + "tune", data=b"{}",
            headers={"Content-Type": "application/json", "Origin": "https://example.com"},
            method="POST",
        )
        try:
            urlopen(cross_origin, timeout=2)
        except HTTPError as response:
            assert response.code == 403
        else:
            raise AssertionError("a cross-origin request reached localhost")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    print("OK")


if __name__ == "__main__":
    test()
