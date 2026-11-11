# Investigation trace index

Full arguments, results and provider responses are in trace.jsonl.

- discovery: model openai/gpt-oss-120b / completed / usage {"input_tokens": 828, "output_tokens": 26, "total_tokens": 854}
- discovery: tool discover; result index returned; elapsed 1.375s
- discovery: model openai/gpt-oss-120b / completed / usage {"input_tokens": 1249, "output_tokens": 69, "total_tokens": 1318}
- discovery: tool read_issue; result None; elapsed 2.547s
- discovery: model openai/gpt-oss-120b / completed / usage {"input_tokens": 2193, "output_tokens": 118, "total_tokens": 2311}
- discovery: tool declare_requirements; result True; elapsed 3.297s
- REQ-01: model openai/gpt-oss-120b / completed / usage {"input_tokens": 1693, "output_tokens": 140, "total_tokens": 1833}
- REQ-01: tool read_issue; result None; elapsed 4.922s
- REQ-01: model openai/gpt-oss-120b / completed / usage {"input_tokens": 2212, "output_tokens": 126, "total_tokens": 2338}
- REQ-01: tool read_issue; result None; elapsed 7.734s
- REQ-01: model openai/gpt-oss-120b / completed / usage {"input_tokens": 2748, "output_tokens": 187, "total_tokens": 2935}
- REQ-01: tool read_issue; result None; elapsed 23.422s
- REQ-01: model openai/gpt-oss-120b / completed / usage {"input_tokens": 3257, "output_tokens": 188, "total_tokens": 3445}
- REQ-01: tool verify_evidence_scope; result None; elapsed 45.094s
- REQ-01: model openai/gpt-oss-120b / completed / usage {"input_tokens": 3504, "output_tokens": 100, "total_tokens": 3604}
- REQ-01: tool read_issue; result None; elapsed 66.141s
- REQ-01: model openai/gpt-oss-120b / completed / usage {"input_tokens": 4448, "output_tokens": 251, "total_tokens": 4699}
- REQ-01: tool verify_evidence_scope; result None; elapsed 101.672s
- REQ-01: model openai/gpt-oss-120b / completed / usage {"input_tokens": 4694, "output_tokens": 831, "total_tokens": 5525}
- REQ-01: requirement_failure; Global tool/time/token budget exhausted
- REQ-02: requirement_failure; Global tool/time/token budget exhausted
- REQ-03: requirement_failure; Global tool/time/token budget exhausted
- REQ-04: requirement_failure; Global tool/time/token budget exhausted
- REQ-05: requirement_failure; Global tool/time/token budget exhausted
- REQ-06: requirement_failure; Global tool/time/token budget exhausted
- REQ-07: requirement_failure; Global tool/time/token budget exhausted
- REQ-08: requirement_failure; Global tool/time/token budget exhausted
- REQ-09: requirement_failure; Global tool/time/token budget exhausted
- REQ-10: requirement_failure; Global tool/time/token budget exhausted
- REQ-11: requirement_failure; Global tool/time/token budget exhausted
- REQ-12: requirement_failure; Global tool/time/token budget exhausted
