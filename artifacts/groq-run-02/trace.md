# Investigation trace index

Full arguments, results and provider responses are in trace.jsonl.

- discovery: model openai/gpt-oss-120b / completed / usage {"input_tokens": 1017, "output_tokens": 30, "total_tokens": 1047}
- discovery: tool discover; result index returned; elapsed 1.203s
- discovery: model openai/gpt-oss-120b / completed / usage {"input_tokens": 1438, "output_tokens": 271, "total_tokens": 1709}
- discovery: tool declare_requirements; result Discover and read the manifest before declaring requirements; elapsed 2.156s
- discovery: model openai/gpt-oss-120b / completed / usage {"input_tokens": 1527, "output_tokens": 52, "total_tokens": 1579}
- discovery: tool read_issue; result None; elapsed 3.735s
- discovery: model openai/gpt-oss-120b / completed / usage {"input_tokens": 2471, "output_tokens": 106, "total_tokens": 2577}
- discovery: tool read_issue; result None; elapsed 5.125s
- run: failure; API request failed: HTTP 400; POST /openai/v1/chat/completions; Tool call validation failed: tool call validation failed: attempted to call tool 'get_linked_issues' which was not in request.tools
