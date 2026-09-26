# Local Operations Brief with LM Studio

A local tool that turns an operations note into a structured handoff brief. It uses LM Studio's OpenAI-compatible API and a JSON schema, then validates the returned fields before saving a record. The example note concerns a fictional inference workstation; it does not describe a real incident.

This project complements [RTX Local LLM Lab](https://github.com/agammann/rtx-local-llm-lab): that project measures Ollama inference on an RTX GPU, while this one uses LM Studio to produce a reviewable operations artifact.

## What it does

- Separates reported observations, unknowns, and proposed non-destructive checks.
- Requires a schema-conforming response with a bounded priority and handoff note.
- Records the source note, model identifier, elapsed time, and API token usage alongside the brief.
- Restricts the API destination to a local HTTP address (`127.0.0.1`, `localhost`, or `::1`).

## Run locally

1. Install [LM Studio](https://lmstudio.ai/) and run these verified CLI commands to download and load Qwen3 4B Instruct Q4_K_M on a compatible GPU:

   ```powershell
   lms get "https://huggingface.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF" --gguf --yes
   lms load qwen3-4b-instruct-2507 --gpu max --context-length 2048 --identifier qwen3-4b-instruct-2507 --yes
   lms server start --port 1234 --bind 127.0.0.1
   ```

2. Run:

   ```powershell
   python .\ops_brief.py --model YOUR_MODEL_ID --output .\examples\sample-brief.json
   python -m unittest -v
   ```

The default note is a sample. For your own note, add `--incident "your observation"`. The script uses only Python's standard library. Another instruction model may work if it supports LM Studio structured output; set its actual API identifier in `--model`.

## Local verification

Tested with LM Studio 0.4.25+1 and Qwen3 4B Instruct 2507 Q4_K_M on an NVIDIA GeForce RTX 3050 6GB Laptop GPU. The model loaded with `--gpu max` and a 2048-token context. The included [sample brief](examples/sample-brief.json) is an actual local API response; its timing and token usage are for that one run, not a performance guarantee. Four validation tests passed.

## Output contract

The `brief` object contains `reported_facts`, `unknowns`, `next_checks`, `priority`, and `handoff_note`. Each list must contain 1 to 4 nonempty strings; priority must be `low`, `normal`, or `urgent`. The program rejects missing or extra fields and exits without writing a brief when validation fails.

Schema validation checks format, not factual accuracy. Review the brief against the source note before using it in an operational decision. Small models can still misstate facts or propose unhelpful checks.

## References

- [LM Studio OpenAI-compatible API](https://lmstudio.ai/docs/developer/openai-compat)
- [LM Studio structured output](https://lmstudio.ai/docs/developer/openai-compat/structured-output)
- [LM Studio CLI and local server](https://lmstudio.ai/docs/cli)

MIT licensed. See [LICENSE](LICENSE).

