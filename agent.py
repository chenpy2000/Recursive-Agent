import argparse
import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "Return the current date and time in UTC.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }
]


def current_time() -> str:
    return datetime.now(timezone.utc).isoformat()


async def ask(question: str) -> str:
    load_dotenv(Path(__file__).with_name(".env"))
    provider = os.getenv("PROVIDER", "").strip().lower()
    if provider not in {"deepinfra", "openrouter"}:
        raise ValueError("Set PROVIDER to deepinfra or openrouter in .env.")

    prefix = provider.upper()
    settings = [os.getenv(f"{prefix}_{key}", "").strip()
                for key in ("API_KEY", "BASE_URL", "MODEL")]
    if not all(settings):
        raise ValueError(f"Fill in {prefix}_API_KEY, {prefix}_BASE_URL and {prefix}_MODEL in .env.")
    api_key, base_url, model = settings

    messages = [{"role": "user", "content": question}]
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
                if call.function.name != "current_time":
                    raise ValueError(f"Unknown tool: {call.function.name}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": current_time(),
                })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ask an LLM a question.")
    parser.add_argument("question")
    args = parser.parse_args()
    print(asyncio.run(ask(args.question)))
