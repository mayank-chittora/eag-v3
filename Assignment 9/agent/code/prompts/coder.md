Placeholder prompt for the Coder skill. Replace this with a prompt that
takes an input task and emits Python code in JSON shape:
`{"code": "<python>", "rationale": "<one line>"}`. The orchestrator
will hand the code to `sandbox_executor` next (declared as a static
internal successor in agent_config.yaml).
