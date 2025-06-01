import json
from contextlib import _AsyncGeneratorContextManager
from typing import Any, AsyncGenerator

import httpx
from nonebot.log import logger


class APIError(Exception):
    """基础API异常类"""

    def __init__(self, message: str, code: int | None = None):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}" if code else message)


class AsyncChatClient:
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        timeout: int = 120,
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.close()

    async def close(self):
        await self._client.aclose()

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create(self, model: str, messages: list[dict[str, Any]], **kwargs) -> dict:
        """发起非流式请求并返回解析后的响应"""
        url = f"{self.endpoint}/chat/completions"
        payload = {"model": model, "messages": messages, "stream": False, **kwargs}

        response = await self._client.post(url, headers=self._build_headers(), json=payload, timeout=self.timeout)

        if response.status_code != 200:
            await self._handle_error(response)

        return response.json()

    def stream_create(self, model: str, messages: list[dict[str, Any]], **kwargs) -> AsyncGenerator[str, None]:
        """发起流式请求并返回异步生成器"""
        url = f"{self.endpoint}/chat/completions"
        payload = {"model": model, "messages": messages, "stream": True, **kwargs}

        response_stream = self._client.stream(
            "POST",
            url,
            headers=self._build_headers(),
            json=payload,
            timeout=self.timeout,
        )

        return self._process_stream(response_stream)

    async def _handle_error(self, response: httpx.Response):
        """统一错误处理"""
        try:
            error_data = response.json()
            message = error_data.get("message", "Unknown error")
            code = error_data.get("code", response.status_code)
        except json.JSONDecodeError:
            message = f"HTTP Error {response.status_code}"
            code = response.status_code
        raise APIError(message, code)

    async def _process_stream(self, response: _AsyncGeneratorContextManager[httpx.Response, None]) -> AsyncGenerator[str, None]:  # type: ignore
        """处理流式响应"""
        self.content = ""
        self.reasoning_content = ""

        async with response as resp:
            if resp.status_code != 200:
                await self._handle_error(resp)

            async for chunk in resp.aiter_lines():
                try:
                    if chunk.startswith("data: "):
                        data_str = chunk[6:].strip()
                        if data_str == "[DONE]":
                            continue

                        data = json.loads(data_str)
                        choice = data["choices"][0]
                        delta = choice.get("delta", {})

                        # 更新内容
                        self.reasoning_content += delta.get("reasoning_content") or ""
                        self.content += delta.get("content") or ""

                        yield self.reasoning_content + self.content
                except json.JSONDecodeError as e:
                    logger.opt(exception=e).error(f"Failed to parse stream chunk: {chunk}")
                    continue
