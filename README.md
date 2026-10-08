# Operations Brief with LM Studio

Turn a short operations note into a reviewable JSON handoff: reported facts, missing evidence, suggested checks, and a short summary. Run a model locally through LM Studio, or explicitly choose OpenAI with your own API key.

The tool checks the response format and keeps the original note beside the result. **Both modes produce drafts that need review.** Real tests found that the local 4B model can change numbers or treat known facts as unknowns. The hosted option improved the tested outputs, but can still suggest redundant checks. See the [dated verification results](VERIFICATION.md) before choosing a mode.

This project complements [RTX Local LLM Lab](https://github.com/agammann/rtx-local-llm-lab), which measures local inference performance. This one explores a practical use of structured output.

## Run locally

Download `lmstudio-local-ops-brief_1.0.0_source.zip` and `SHA256SUMS` from the [v1.0.0 release](https://github.com/agammann/lmstudio-local-ops-brief/releases/tag/v1.0.0), compare the ZIP's SHA-256 digest, and extract it. In PowerShell:

```powershell
Get-FileHash .\lmstudio-local-ops-brief_1.0.0_source.zip -Algorithm SHA256
Expand-Archive .\lmstudio-local-ops-brief_1.0.0_source.zip -DestinationPath .\ops-brief
cd .\ops-brief\lmstudio-local-ops-brief_1.0.0
python .\ops_brief.py --version
python .\ops_brief.py --help
```

Developers can instead clone the pinned tag:

```powershell
git clone --branch v1.0.0 --depth 1 https://github.com/agammann/lmstudio-local-ops-brief.git
cd .\lmstudio-local-ops-brief
```

Requirements: Python 3.10+ and [LM Studio](https://lmstudio.ai/) with its `lms` CLI available. No Python packages are required.

Download Qwen3 4B Instruct Q4_K_M if it is not already installed, then load it and start a loopback server:

```powershell
lms get "https://huggingface.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF" --gguf --yes
lms load qwen3-4b-instruct-2507 --gpu max --context-length 4096 --identifier ops-brief --yes
lms server start --port 1234 --bind 127.0.0.1
python .\ops_brief.py --model ops-brief
```

The default note is fictional. To use your own note and save the result:

```powershell
python .\ops_brief.py --model ops-brief --incident "API p95 latency rose from 20 ms to 80 ms at 08:10 UTC. The cause has not been tested." --output .\brief.json
```

Use the exact identifier shown by `lms ps` if you already have a model loaded. Another instruction model may work if it supports LM Studio structured output. Hardware requirements and generation quality vary; the local mode is experimental.

Only local HTTP destinations (`127.0.0.1`, `localhost`, or `::1`) are accepted in this mode. The script does not send the note or an API key to OpenAI unless you explicitly select the hosted provider. Downloading model weights requires a separate network connection.

When finished with the model and server you started:

```powershell
lms unload ops-brief
lms server stop
```

## Optional hosted mode: use your own key

```powershell
python .\ops_brief.py --provider openai --output .\brief.json
```

In an interactive terminal, enter your OpenAI API key at the hidden prompt. The script does not save it. An existing `OPENAI_API_KEY` environment variable also works for automation; `.env` files are not loaded automatically. Do not put a real key in source code or command history.

Hosted mode sends the complete supplied note to the fixed OpenAI Responses API endpoint using **GPT-5.4 with high reasoning**. It uses your API account and billing, sets `store: false`, and makes one request without automatic retries or provider fallback. `store: false` controls response storage; it does not make the request local. Use `--incident` to replace the same fictional default note shown in local mode.

The project supplies no shared key. `--url` applies only to LM Studio; hosted mode rejects a custom destination or a different model name. Keys are excluded from saved results and error messages. An invalid key produces an HTTP 401 error without replacing an existing result.

## Output and failure behavior

The JSON record includes the original source note, provider, model, UTC timestamp, elapsed time, token usage, and the `brief` object:

| Field | Contract |
| --- | --- |
| `reported_facts` | 1–8 nonempty strings |
| `unknowns` | 1–4 nonempty strings |
| `next_checks` | 1–4 nonempty strings |
| `priority` | `low`, `normal`, or `urgent` |
| `handoff_note` | A nonempty string |

Notes must contain text and be at most 4,000 characters; they are never silently shortened. A character limit does not guarantee that every note fits a model's context or finishes within its output allowance. Local output is limited to 700 tokens, hosted output to 6,000 tokens including reasoning. Keep operational notes concise.

Incomplete responses, refusals, invalid fields, API redirects, and responses larger than 128 KiB are rejected before saving. The HTTP operation has a 180-second timeout. Network errors do not trigger retries. Output files are replaced only after a complete validated result has been written to a temporary file in the same directory. The saved record contains the full input note, so choose its location accordingly.

Schema validation establishes structure, not truth. Check every observation and proposed action against the source. The program does not execute the suggested checks or make changes to a workstation.

## Verification and examples

See the [v1 release checks](RELEASE_VERIFICATION.md) for the current source ZIP and first local/hosted requests. The earlier results below retain their original dates.

```powershell
python -m unittest -v
```

The suite covers schema validation, incomplete output, input limits, credential boundaries, actual HTTP redirect rejection, and preserving an existing file when a save fails. Real local and hosted runs are documented separately in [VERIFICATION.md](VERIFICATION.md), with captured responses for four fictional cases.

## Keep, recover and update

Saved `brief.json` files contain the full source note. Keep them outside the extracted application folder, open them in a text editor to review the source beside the draft, and copy them to your normal backup location. Restore by copying the saved JSON back; this CLI has no separate account or hidden workspace database.

If a local request fails, check `lms ps` and `lms server status`, confirm the identifier and loopback port, and try a shorter note. An input, model or save failure preserves an existing output file. Hosted errors identify authentication, connection or completion failure without automatic retries. Keep the existing result until a new draft has been reviewed.

For an update, extract the new release into a new folder, verify its checksum and `--version`, run `python -m unittest -v`, and retain your saved briefs before switching. Remove the old application folder when satisfied. Stop only the LM Studio model/server you started; model downloads live in LM Studio's separate model library.

To change the implementation, edit `ops_brief.py` and run the existing unit suite. From a clean committed Git checkout, `python scripts/package-release.py` creates the source ZIP and `python scripts/check-consumer.py` verifies a fresh extraction. Windows and Ubuntu CI cover Python 3.10 and 3.14. Report a reproducible problem through [GitHub Issues](https://github.com/agammann/lmstudio-local-ops-brief/issues), including the version and redacted error; omit API keys and private operations notes.

The source is [MIT licensed](LICENSE). Model weights are separate downloads governed by their own licenses.

The [original sample](examples/sample-brief.json) is a historical local response from September 26, 2026. It predates the provider field and current verification; its timing is not a performance guarantee.

## References

- [LM Studio OpenAI-compatible API](https://lmstudio.ai/docs/developer/openai-compat)
- [LM Studio structured output](https://lmstudio.ai/docs/developer/openai-compat/structured-output)
- [LM Studio CLI](https://lmstudio.ai/docs/cli)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/create)

MIT licensed. See [LICENSE](LICENSE).
