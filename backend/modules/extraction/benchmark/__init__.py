"""Sprint-0 benchmark harness (issue #3).

Measures per-provider, per-field accuracy + latency (p50/p95) + cost/doc over a
manifest of PII-scrubbed contract samples. Produces the data behind
docs/benchmark_vision_extraction_v0.1.md.

Run: see runner.py module docstring. The harness never invents numbers — with no
API keys / no samples it reports failures honestly.
"""
