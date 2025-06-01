import base64
import ssl
import time
from io import BytesIO

import httpx
from nonebot import get_plugin_config, logger
from nonebot_plugin_alconna.uniseg import Image
from PIL import Image as PILImage

from ..api import AsyncChatClient
from ..config import Config

config = get_plugin_config(Config)


async def url_to_base64(url: str) -> str:
    """将URL图片转换为base64编码

    Args:
        url: 图片URL

    Returns:
        str: base64编码的图片数据
    """
    ssl_context = ssl.create_default_context()
    ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_3
    ssl_context.set_ciphers("HIGH:!aNULL:!MD5")

    async with httpx.AsyncClient(verify=ssl_context) as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.opt(exception=e).error(f"获取图片失败: {url}, 错误: {e}")
            raise

        image = PILImage.open(BytesIO(response.content))
        # 把图片控制在5mb以内
        if len(response.content) > 5 * 1024 * 1024:
            image.thumbnail((4096, 4096))
        if image.mode != "RGB":
            image = image.convert("RGB")

        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=80)
        b64_content = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64_content}"


async def process_image(image: Image) -> str | None:
    """处理图片内容, 返回图片描述

    Args:
        image: 图片对象

    Returns:
        Optional[str]: 图片描述内容, 失败时返回None
    """
    if not image.url or not config.zssm_ai_vl_token:
        return None

    try:
        logger.info(f"开始处理图片: {config.zssm_ai_vl_model}")
        async with AsyncChatClient(config.zssm_ai_vl_endpoint, config.zssm_ai_vl_token) as client:
            logger.info(f"处理图片: {image.url}")
            last_time = time.time()
            last_chunk = ""
            i = 0

            async for chunk in client.stream_create(
                config.zssm_ai_vl_model,
                [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": await url_to_base64(image.url)},
                            },
                            {
                                "type": "text",
                                "text": "请你作为你文本模型姐妹的眼睛, 告诉她这张图片的内容",
                            },
                        ],
                    },
                ],
            ):
                i += 1
                last_chunk = chunk
                if time.time() - last_time > 5:
                    last_time = time.time()
                    small_chunk = f"{chunk[:20]}...{len(chunk) - 40}...{chunk[-20:]}" if len(chunk) > 60 else chunk
                    logger.info(f"图片处理进度: {i}, {small_chunk}")

            logger.info(f"图片处理完成: {i}, {last_chunk}")
            return client.content

    except Exception as e:
        logger.opt(exception=e).error(f"图片处理失败: {e}")
        return None
