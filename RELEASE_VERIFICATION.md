# Version 1.0.0 verification

The current source was tested on Windows with Python 3.12.14 and LM Studio 0.4.25. Twelve unit tests passed. A fresh source ZIP extracted into a path containing spaces also passed the unit suite, version/help commands and rejection of an empty note without replacing the previous saved JSON. The release workflow checks Python 3.10 and 3.14 on Windows and Ubuntu before publishing the source and its checksums.

The first current local and hosted requests used the same fictional note: the CPU alarm threshold is 90%, the only captured reading is 13%, GPU utilization was not collected, requests are succeeding, and no configuration change, restart or rollback is approved. Both saved records retained the complete source and kept the threshold and reading distinct. No quality retry replaced either first response.

- Local Qwen3 4B Instruct 2507 Q4_K_M completed through LM Studio's loopback server in about 6.1 seconds with a 4,096-token context. It preserved the source in its handoff, but reopened the already answered GPU-measurement question and proposed extra checks. This remains an experimental draft mode.
- Visitor-key GPT-5.4, returned as `gpt-5.4-2026-03-05` with high reasoning, completed through the actual CLI in about 8.5 seconds. Its facts and handoff preserved all five source observations and its next checks did not request an unapproved state change. Some suggestions still recheck stated observations; review them before use.

The local model came from the existing LM Studio cache; this run did not repeat its weight download. The owned test model was unloaded and the loopback server stopped afterward. Individual timings describe these requests, not a performance benchmark.

[Earlier four-case results and retained adverse responses](VERIFICATION.md) remain dated separately. The output schema checks structure, and the saved source makes factual review possible. The program executes no suggested action.
