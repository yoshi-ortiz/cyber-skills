#!/usr/bin/env python3
"""Send compiled image prompts to external raster generation adapters."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run_moodboard(project_root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    from graphics_corpus import refine_references
    from text_to_graphics import (GraphicsError, _read_json, _sha256_bytes,
                                  append_attempt, compile_slices, load_manifest)

    manifest = load_manifest(project_root)
    pending = refine_references(project_root)
    if pending:
        raise GraphicsError(
            "refine-tagged attempts are pending; edit or reuse them before spending "
            "a fresh moodboard shot: " + ", ".join(path for path, _ in pending))
    compile_slices(project_root)
    agy = ((manifest.get("adapters") or {}).get("agy") or {})
    model = agy.get("imageModel", "gemini-3.1-flash-image-preview")
    compiled = project_root / "moodboards/llm-shots/prompts/graphics-prompt.json"
    prompt = _read_json(compiled)["prompt"]
    attempts_dir = project_root / str(
        (manifest.get("outputs") or {}).get("moodboardAttempts")
        or "moodboards/llm-shots/attempts")
    attempts_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    record = {
        "adapter": "agy", "model": model,
        "promptHash": _sha256_bytes(prompt.encode("utf-8")),
        "promptBytes": len(prompt.encode("utf-8")),
        "outcome": "pending", "note": "moodboard only; not deliverable",
    }
    if dry_run:
        record["command"] = (
            f"agy --dangerously-skip-permissions --print-timeout 15m -p "
            f"'Call generate_image once: AspectRatio 16:9, model {model}, "
            f"Prompt from {compiled}'")
        append_attempt(project_root, record)
        return record

    instruction = (
        "Call generate_image exactly once with AspectRatio 16:9, "
        f"ImageName moodboard_{stamp}, and the Prompt below. "
        f"Save PNG under {attempts_dir}/. Print path or error.\n\n{prompt}")
    cmd = ["agy", "--dangerously-skip-permissions", "--print-timeout", "15m",
           "-p", instruction]
    completed = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    record.update({"exitCode": completed.returncode,
                   "stdoutTail": completed.stdout[-2000:],
                   "stderrTail": completed.stderr[-2000:],
                   "outcome": "pending" if completed.returncode == 0 else "rejected"})
    append_attempt(project_root, record)
    if completed.returncode != 0:
        raise GraphicsError(f"agy moodboard failed: {completed.stderr[-500:]}")
    return record


def run_clear_shot(project_root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    from graphics_slices import clear_shot_prompt
    from text_to_graphics import (GraphicsError, _sha256_bytes, append_attempt,
                                  load_manifest)

    manifest = load_manifest(project_root)
    prompt_record = clear_shot_prompt(project_root)
    prompt_path = Path(prompt_record["clearShotPrompt"])
    prompt = prompt_path.read_text(encoding="utf-8")
    agy = ((manifest.get("adapters") or {}).get("agy") or {})
    model = str(agy.get("imageModel") or "gemini-3.1-flash-image-preview")
    aspect = str(agy.get("aspectRatio") or "16:9")
    attempts_dir = project_root / str(
        (manifest.get("outputs") or {}).get("moodboardAttempts")
        or "moodboards/llm-shots/attempts")
    attempts_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = attempts_dir / f"clear-shot-{stamp}.png"
    instruction = (
        "Read the target and character reference images named in the prompt before "
        "you generate anything. Call generate_image exactly once. Use image model "
        f"{model} and aspect ratio {aspect}. Treat the target as the image to edit, "
        "not as loose inspiration. Pass the target and character images to the image "
        "tool as references. Save or copy the final PNG to this exact path: "
        f"{output}. Do not modify the source images. Return the final path.\n\n{prompt}")
    cmd = ["agy", "--dangerously-skip-permissions", "--print-timeout", "15m",
           "--output-format", "json", "-p", instruction]
    record = {
        "adapter": "agy", "model": model,
        "prompt": str(prompt_path), "output": str(output),
        "promptHash": _sha256_bytes(prompt.encode("utf-8")),
        "promptBytes": len(prompt.encode("utf-8")),
        "outcome": "pending", "note": "clear-shot image proposal",
    }
    if dry_run:
        record["command"] = " ".join(cmd[:-1]) + " <generated clear-shot prompt>"
        append_attempt(project_root, record)
        return record

    completed = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    response = completed.stdout
    try:
        payload = json.loads(completed.stdout)
        response = str(payload.get("response") or payload.get("error") or "")
        cli_success = payload.get("status") in (None, "SUCCESS")
    except json.JSONDecodeError:
        cli_success = completed.returncode == 0
    success = completed.returncode == 0 and cli_success and output.is_file()
    record.update({"exitCode": completed.returncode,
                   "stdoutTail": completed.stdout[-2000:],
                   "stderrTail": completed.stderr[-2000:],
                   "outcome": "pending" if success else "rejected"})
    append_attempt(project_root, record)
    if not success:
        detail = completed.stderr[-500:] or response[-500:] or "PNG was not written"
        raise GraphicsError(f"agy clear-shot generation failed: {detail}")
    return record
