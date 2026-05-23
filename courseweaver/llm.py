from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


class LLMError(RuntimeError):
    pass


class OpenAICompatibleClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "",
        base_url: str = "",
        api_key_env: str = "",
        timeout: int = 120,
        extra_body: dict | None = None,
        token_field: str = "max_tokens",
    ) -> None:
        self.api_key = api_key if api_key is not None else load_api_key(api_key_env)
        if not self.api_key:
            raise LLMError(f"{api_key_env} is required when --use-llm is enabled.")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.extra_body = extra_body or {}
        self.token_field = token_field

    def chat(self, messages: list[dict[str, str]], max_tokens: int = 1800, temperature: float = 0.3) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
            self.token_field: max_tokens,
        }
        payload.update(self.extra_body)
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LLMError(f"LLM API error {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"LLM API request failed: {exc.reason}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected LLM response: {data}") from exc
        return content.strip()


class DeepSeekClient(OpenAICompatibleClient):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "deepseek-v4-pro",
        base_url: str = "https://api.deepseek.com",
        timeout: int = 120,
        thinking: str = "disabled",
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            api_key_env="DEEPSEEK_API_KEY",
            timeout=timeout,
            extra_body={"thinking": {"type": thinking}},
            token_field="max_tokens",
        )


class KimiClient(OpenAICompatibleClient):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "kimi-k2.6",
        base_url: str = "https://api.moonshot.ai/v1",
        timeout: int = 120,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            api_key_env="MOONSHOT_API_KEY",
            timeout=timeout,
            token_field="max_completion_tokens",
        )


DeepSeekError = LLMError


def load_api_key(api_key_env: str, dotenv_path: Path | str = ".env") -> str:
    env_value = os.environ.get(api_key_env, "").strip()
    if env_value:
        return env_value

    path = Path(dotenv_path)
    if not path.exists():
        return ""

    raw_lines = path.read_text(encoding="utf-8").splitlines()
    for line in raw_lines:
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        key, value = clean.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == api_key_env:
            return value

    meaningful_lines = [
        line.strip()
        for line in raw_lines
        if line.strip() and not line.strip().startswith("#") and "=" not in line
    ]
    if api_key_env == "DEEPSEEK_API_KEY" and len(meaningful_lines) == 1:
        return meaningful_lines[0].strip().strip('"').strip("'")
    return ""


def create_llm_client(
    provider: str,
    api_key: str | None = None,
    model: str | None = None,
    thinking: str = "disabled",
):
    normalized = provider.strip().lower()
    if normalized == "deepseek":
        return DeepSeekClient(api_key=api_key, model=model or "deepseek-v4-pro", thinking=thinking)
    if normalized in {"kimi", "moonshot"}:
        return KimiClient(api_key=api_key, model=model or "kimi-k2.6")
    raise LLMError(f"Unsupported LLM provider: {provider}")
