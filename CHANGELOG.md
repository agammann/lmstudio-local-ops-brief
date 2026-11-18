# Changelog

## 1.0.1

Local LM Studio requests now bypass automatic proxy configuration. Hosted requests retain Python's usual proxy selection, and both providers continue rejecting redirects. New handler-construction checks cover the local and hosted boundaries without routing a note through a proxy.

## 1.0.0

The first versioned source release packages the reviewed operations-note CLI with a matching version command, checksums and fresh Python consumer checks. Local LM Studio and optional visitor-key GPT-5.4 produce drafts for human review. The original note stays with each saved JSON result; failed requests and saves preserve an existing result.
