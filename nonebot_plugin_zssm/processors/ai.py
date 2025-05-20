import json
import re
import time
from pathlib import Path

from nonebot import get_plugin_config, logger

from ..api import AsyncChatClient
from ..config import Config

# 从文件加载系统提示词
SYSTEM_PROMPT_RAW = (
    Path(__file__).parent.parent.joinpath("prompt.txt").read_text(encoding="utf-8")
)
config = get_plugin_config(Config)


async def generate_ai_response(system_prompt: str, user_prompt: str) -> str | None:
    """生成AI响应

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词

    Returns:
        Optional[str]: AI生成的响应, 失败时返回None
    """
    if not config.zssm_ai_text_token:
        return None

    try:
        async with AsyncChatClient(
            config.zssm_ai_text_endpoint, config.zssm_ai_text_token
        ) as client:
            last_time = time.time()
            last_chunk = ""
            i = 0

            async for chunk in client.stream_create(
                config.zssm_ai_text_model,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            ):
                try:
                    i += 1
                    last_chunk = chunk
                    if time.time() - last_time > 5:
                        last_time = time.time()
                        small_chunk = (
                            f"{chunk[:20]}...{len(chunk) - 40}...{chunk[-20:]}"
                            if len(chunk) > 60
                            else chunk
                        )
                        logger.info(f"AI响应进度: {i}, {small_chunk}")
                except Exception as e:
                    logger.error(f"处理AI响应块失败: {e}")

            logger.info(f"AI响应完成: {i}")
            print(last_chunk)  # noqa: T201

            data: str = client.content
            if not data:
                logger.error("AI返回内容为空")
                return None

            # 尝试清理Markdown代码块
            try:
                markdown_pattern = r"^```\w*\s*|\s*```$"
                data = re.sub(markdown_pattern, "", data.strip())
            except Exception as e:
                logger.warning(f"清理Markdown格式失败: {e}")

            # 尝试解析JSON
            try:
                # 记录原始内容用于调试
                logger.debug(f"尝试解析JSON: {data}")

                # 防御性解析，尝试修复常见问题
                if data.startswith("```json") and data.endswith("```"):
                    data = data[7:-3].strip()

                llm_output = json.loads(data)

                # 检查必要字段
                if "output" not in llm_output:
                    logger.error(f"AI响应缺少output字段: {data}")
                    return "（AI回复内容异常，请重试）"

                if llm_output.get("block", True):
                    return "（抱歉, 我现在还不会这个）"

                if llm_output.get("keyword"):
                    keywords = llm_output["keyword"]
                    if isinstance(keywords, list):
                        return (
                            f"关键词：{' | '.join(keywords)}\n\n{llm_output['output']}"
                        )
                    return f"关键词：{keywords}\n\n{llm_output['output']}"

                return llm_output["output"]

            except json.JSONDecodeError as e:
                logger.opt(exception=e).error(f"JSON解析失败: {data}")
                return None

    except KeyError as e:
        logger.opt(exception=e).error("缺少必要字段")
        return None
    except Exception as e:
        logger.opt(exception=e).error("生成AI响应失败")
        return None
