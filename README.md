# Minimal async agent

One Python file using `AsyncOpenAI`, with tools for the current UTC time and
spawning a child agent. The agent sends your question to the model, executes
requested tools, and sends the results back until the model answers.

The `spawn_agent` tool runs the exact same `ask` function as the main agent,
with the same model, system instructions, and tools in a fresh conversation.
The parent waits for the child's answer, receives it as a tool result, and
continues working. Children can recursively delegate smaller subtasks. Each
child sees only its supplied prompt and the shared system instructions, so the
parent must include all necessary context. Multiple tool calls run sequentially.
The instructions encourage decomposition when useful and direct answers for
simple tasks. Set `MAX_RECURSIVE_DEPTH=5` in `.env` to allow five levels of
children below the main agent (depth 0). At depth 5, spawning returns a limit
message instead of creating another child, and the agent continues solving its
task. Set it to 0 to disable spawning. The depth is tracked by Python, not the LLM.

## Run

```sh
uv sync
```

Edit `.env`. Set `PROVIDER` to
`deepinfra` or `openrouter`, then fill in that provider's API key and model ID.
Use a model that supports function/tool calling. The other provider can stay blank.
Here, DeepInfra/HF means Hugging Face models hosted by DeepInfra.

```sh
uv run python agent.py "What time is it now? Use your time tool."
uv run python agent.py "What is recursion?"
uv run python agent.py "Plan a small Python CLI. Delegate its testing plan to a child agent, then incorporate the result."
```

`.env` is ignored by Git. Existing environment variables take precedence over it.
Requests specify only the model, messages, and tool definition; no temperature,
token limits, or other generation settings are added.

## Verify

```sh
uv run python -m unittest discover -s tests -v
```

Tests simulate model responses without making paid API calls, including nested
delegation and the parent continuing after a child returns.

## References

- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [DeepInfra OpenAI-compatible API](https://docs.deepinfra.com/chat/overview)
- [OpenRouter quickstart](https://openrouter.ai/docs/quickstart)
