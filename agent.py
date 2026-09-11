import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI


SYSTEM_PROMPT = (
    "In order to solve the current problem, find the next step to do. "
    "When that step benefits from delegation, provide all details necessary "
    "in a self-contained prompt and use spawn_agent to assign it to a new agent. "
    "Delegate a smaller, concrete subtask, not the whole problem unchanged. "
    "Use the returned result to continue your work and answer the original question. "
    "If spawning is refused because the recursive depth limit is reached, solve the task yourself. "
    "Solve simple tasks directly; do not spawn an agent when no decomposition is needed."
)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "Return the current date and time in UTC.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_agent",
            "description": (
                "Spawn an agent for a smaller next step and wait for its answer. "
                "Include the subtask, relevant context, and desired result in the prompt. "
                "The child has the same tools and can delegate further."
            ),
            "parameters": {
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
                "additionalProperties": False,
            },
        },
    },
]


def current_time() -> str:
    return datetime.now(timezone.utc).isoformat()


async def spawn_agent(prompt: str, depth: int, max_depth: int) -> str:
    if depth >= max_depth:
        return "Maximum recursive depth reached. Solve this task directly without spawning another agent."
    return await ask(prompt, depth=depth + 1)


async def ask(question: str, depth: int = 0) -> str:
    load_dotenv(Path(__file__).with_name(".env"))
    max_depth = int(os.getenv("MAX_RECURSIVE_DEPTH", "5"))
    if max_depth < 0:
        raise ValueError("MAX_RECURSIVE_DEPTH must be non-negative.")
    provider = os.getenv("PROVIDER", "").strip().lower()
    if provider not in {"deepinfra", "openrouter"}:
        raise ValueError("Set PROVIDER to deepinfra or openrouter in .env.")

    prefix = provider.upper()
    settings = [os.getenv(f"{prefix}_{key}", "").strip()
                for key in ("API_KEY", "BASE_URL", "MODEL")]
    if not all(settings):
        raise ValueError(f"Fill in {prefix}_API_KEY, {prefix}_BASE_URL and {prefix}_MODEL in .env.")
    api_key, base_url, model = settings

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    async with AsyncOpenAI(api_key=api_key, base_url=base_url) as client:
        while True:
            response = await client.chat.completions.create(
                model=model, messages=messages, tools=TOOLS
            )
            message = response.choices[0].message
            if not message.tool_calls:
                return message.content or ""

            messages.append(message.model_dump(exclude_none=True))
            for call in message.tool_calls:
                if call.type != "function":
                    raise ValueError(f"Unsupported tool call type: {call.type}")
                if call.function.name == "current_time":
                    result = current_time()
                elif call.function.name == "spawn_agent":
                    arguments = json.loads(call.function.arguments)
                    result = await spawn_agent(arguments["prompt"], depth, max_depth)
                else:
                    raise ValueError(f"Unknown tool: {call.function.name}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ask an LLM a question.")
    parser.add_argument("question")
    args = parser.parse_args()
    print(asyncio.run(ask(args.question)))
