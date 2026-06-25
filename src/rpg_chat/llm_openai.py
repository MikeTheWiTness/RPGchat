import os
from openai import OpenAI, APITimeoutError, APIConnectionError

from rpg_chat.llm import LLMProvider


class LLMTimeoutError(Exception):
    """LLM 调用超时或连接失败，用于上层友好兜底。"""
    pass


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        reasoning_effort: str | None = None,
        timeout: int | None = None,
    ):
        self._api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self._base_url = base_url or "https://api.deepseek.com"
        self._model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
        self._reasoning_effort = reasoning_effort or os.environ.get(
            "DEEPSEEK_REASONING_EFFORT", "high"
        )
        self._timeout = timeout or int(os.environ.get("DEEPSEEK_TIMEOUT", "120") or 120)

        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        messages = []
        system_content = system_prompt or (
            "你是一个 TRPG 游戏主持人助手。你需要根据给定的上下文，"
            "严格依照指令返回 JSON 格式的输出，或进行剧情叙述。"
            "不要在 JSON 之外添加额外的解释文字。"
        )
        messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=False,
                timeout=self._timeout,
                reasoning_effort=self._reasoning_effort,
                extra_body={"thinking": {"type": "enabled"}},
            )
        except (APITimeoutError, APIConnectionError) as e:
            raise LLMTimeoutError(f"LLM 响应超时或连接失败: {e}") from e
        return response.choices[0].message.content
