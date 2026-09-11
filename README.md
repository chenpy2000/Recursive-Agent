# Minimal async agent

One Python file using `AsyncOpenAI`, with one tool that returns the current UTC
time. The agent sends your question to the model, executes any requested time
tool calls, and sends the results back until the model answers.

## Run

```sh
uv sync
```

Edit `.env` (copy `.env.example` if cloning the repository). Set `PROVIDER` to
`deepinfra` or `openrouter`, then fill in that provider's API key and model ID.
Use a model that supports function/tool calling. The other provider can stay blank.
Here, DeepInfra/HF means Hugging Face models hosted by DeepInfra.

```sh
uv run python agent.py "What time is it now? Use your time tool."
uv run python agent.py "What is recursion?"
```

`.env` is ignored by Git. Existing environment variables take precedence over it.
Requests specify only the model, messages, and tool definition; no temperature,
token limits, or other generation settings are added.

## References

- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [DeepInfra OpenAI-compatible API](https://docs.deepinfra.com/chat/overview)
- [OpenRouter quickstart](https://openrouter.ai/docs/quickstart)
