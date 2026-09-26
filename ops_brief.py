"""Turn a local operations note into a structured, reviewable brief."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


SAMPLE_INCIDENT = (
    "Sample: After an inference workstation reboot, the first model response "
    "takes about 45 seconds; later responses take 2-3 seconds. GPU placement "
    "and model-load timing have not been checked. No customer outage is reported."
)

BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "reported_facts": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 4},
        "unknowns": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 4},
        "next_checks": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 4},
        "priority": {"type": "string", "enum": ["low", "normal", "urgent"]},
        "handoff_note": {"type": "string"},
    },
    "required": ["reported_facts", "unknowns", "next_checks", "priority", "handoff_note"],
    "additionalProperties": False,
}


def validate_brief(brief):
    expected = set(BRIEF_SCHEMA["required"])
    if not isinstance(brief, dict) or set(brief) != expected:
        raise ValueError("response has missing or unexpected fields")
    for field in ("reported_facts", "unknowns", "next_checks"):
        value = brief[field]
        if not isinstance(value, list) or not 1 <= len(value) <= 4:
            raise ValueError(f"{field} must contain 1-4 items")
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError(f"{field} must contain nonempty strings")
    if brief["priority"] not in ("low", "normal", "urgent"):
        raise ValueError("priority must be low, normal, or urgent")
    if not isinstance(brief["handoff_note"], str) or not brief["handoff_note"].strip():
        raise ValueError("handoff_note must be a nonempty string")
    return brief


def post_json(base_url, path, payload):
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="model identifier shown by LM Studio")
    parser.add_argument("--url", default="http://127.0.0.1:1234")
    parser.add_argument("--incident", default=SAMPLE_INCIDENT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    address = urlparse(args.url)
    if address.scheme != "http" or address.hostname not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("--url must be a local HTTP address")

    request = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": (
                "Write an operations handoff brief from the user note. Put only explicitly "
                "reported observations in reported_facts. Put missing evidence in unknowns. "
                "Offer non-destructive checks only. Do not assert or suggest a root cause, "
                "even a likely one; avoid explanations such as warm-up unless stated in the note. "
                "Do not invent metrics or other workstations. "
                "Use urgent only for a reported outage or safety issue."
            )},
            {"role": "user", "content": args.incident},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "operations_brief", "strict": True, "schema": BRIEF_SCHEMA},
        },
        "temperature": 0,
        "max_tokens": 350,
        "stream": False,
    }

    try:
        started = time.perf_counter()
        reply = post_json(args.url, "/v1/chat/completions", request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        content = reply["choices"][0]["message"]["content"]
        brief = validate_brief(json.loads(content))
        result = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "model": reply.get("model", args.model),
            "source_incident": args.incident,
            "elapsed_ms": elapsed_ms,
            "usage": reply.get("usage"),
            "brief": brief,
        }
        rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Saved {args.output}")
        else:
            print(rendered)
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError) as exc:
        print(f"Could not produce a validated brief: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

