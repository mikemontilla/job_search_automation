import json
import os

import anthropic
import yaml
from dotenv import load_dotenv

from src.agent.tools.definitions import TOOLS
from src.agent.tools.router import dispatch
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.config import CONFIG_DIR

load_dotenv()

def _load_config() -> dict:
    path = CONFIG_DIR / "agent_config.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    return {}

_config = _load_config()
MODEL = _config.get("model", "claude-sonnet-4-6")
MAX_TOKENS = _config.get("max_tokens", 4096)


class JobAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.messages: list[dict] = []

    def _tool_result_content(self, tool_use_id: str, result) -> dict:
        if isinstance(result, str):
            content = result
        else:
            content = json.dumps(result, ensure_ascii=False)
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": content,
        }

    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})

        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.messages,
            )

            # Collect text and tool_use blocks
            text_parts = []
            tool_calls = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            # Append assistant turn to history
            self.messages.append({"role": "assistant", "content": response.content})

            # If no tool calls, we're done
            if response.stop_reason == "end_turn" or not tool_calls:
                return "\n".join(text_parts)

            # Execute all tool calls and collect results
            tool_results = []
            for tool_call in tool_calls:
                result = dispatch(tool_call.name, tool_call.input)
                tool_results.append(
                    self._tool_result_content(tool_call.id, result)
                )

            # Send tool results back to the model
            self.messages.append({"role": "user", "content": tool_results})
