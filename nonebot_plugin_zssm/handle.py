import random
import re
from pathlib import Path

import httpx
from arclet.alconna import AllParam
from nonebot import get_plugin_config, logger
from nonebot.internal.adapter import Bot, Event
from nonebot_plugin_alconna import Alconna, Args, Match, on_alconna
from nonebot_plugin_alconna.builtins.extensions.reply import ReplyRecordExtension
from nonebot_plugin_alconna.builtins.uniseg.market_face import MarketFace
from nonebot_plugin_alconna.uniseg import Image, MsgId, Reference, Reply, Text, UniMessage, message_reaction

from .config import Config
from .processors.ai import generate_ai_response
from .processors.image import process_image
from .processors.pdf import process_pdf
from .processors.web import process_web_page

# 从文件加载系统提示词
SYSTEM_PROMPT_RAW = Path(__file__).parent.joinpath("prompt.txt").read_text(encoding="utf-8")
config = get_plugin_config(Config)

zssm = on_alconna(Alconna("zssm", Args["content?", AllParam]), extensions=[ReplyRecordExtension()])


@zssm.handle()
async def handle(msg_id: MsgId, ext: ReplyRecordExtension, event: Event, bot: Bot, content: Match[UniMessage]):
    """处理zssm命令

    Args:
        msg_id: 消息ID
        ext: 回复记录扩展
        event: 事件对象
        bot: 机器人对象
        content: 消息内容
    """
    msg = event.get_message()
    random_number = str(random.randint(10000000, 99999999))  # noqa: S311
    system_prompt = SYSTEM_PROMPT_RAW + random_number
    user_prompt = ""
    image_list: list[Image] = []

    # 处理回复消息
    reply = ext.get_reply(msg_id)
    if reply:
        reply_msg_raw = reply.msg

        if not reply_msg_raw:
            return await UniMessage(Text("上一条消息内容为空")).send(reply_to=Reply(msg_id))

        if isinstance(reply_msg_raw, str):
            reply_msg_raw = msg.__class__(reply_msg_raw)

        reply_msg = UniMessage.generate_sync(message=reply_msg_raw)
        image_list.extend(reply_msg.get(Image))

        reply_msg_display = ""
        for item in reply_msg:
            if isinstance(item, Image):
                reply_msg_display += f"[图片 {hash(item.url)}]"
            elif isinstance(item, Reference):
                return await UniMessage(Text("不支持引用消息")).send(reply_to=Reply(msg_id))
            elif isinstance(item, MarketFace):
                return await UniMessage(Text("不支持商城表情")).send(reply_to=Reply(msg_id))
            reply_msg_display += str(item)

        user_prompt += f"<type: text>\n{reply_msg_display}\n</type: text>"

    # 处理输入内容
    if content.available:
        any_content = content.result
        image_list.extend(any_content.get(Image))

        any_content_display = ""
        for item in any_content:
            if isinstance(item, Image):
                any_content_display += f"[图片 {hash(item.url)}]"
            any_content_display += str(item)

        if reply:
            user_prompt += f"<type: interest>\n{any_content_display}\n</type: interest>"
        else:
            user_prompt += f"<type: text>\n{any_content_display}\n</type: text>"

    if not user_prompt and not image_list:
        return await UniMessage(Text("请回复或输入内容")).send(reply_to=Reply(msg_id))

    # 验证API配置
    if not config.zssm_ai_text_token or not config.zssm_ai_vl_token:
        return await UniMessage(Text("未配置 Api Key, 暂时无法使用")).send(reply_to=Reply(msg_id))

    await message_reaction("424", msg_id, event, bot)

    # 处理图片, 最多2张
    if len(image_list) > 2:
        return await UniMessage(Text("图片数量超过限制, 最多 2 张")).send(reply_to=Reply(msg_id))

    for image in image_list:
        image_content = await process_image(image)
        if image_content:
            user_prompt += f"\n<type: image, id: {hash(image.url)}>\n{image_content}\n</type: image, id: {hash(image.url)}>"
        else:
            return await UniMessage(Text("图片识别失败")).send(reply_to=Reply(msg_id))

    # 处理URL和PDF
    url_pattern = r"\b(?:https?):\/\/[^\s\/?#]+[^\s]*\b"
    pdf_pattern = r"\b(?:https?):\/\/[^\s\/?#]+[^\s]*\.pdf\b"

    # 查找所有URL
    msg_urls = re.findall(url_pattern, str(user_prompt))

    if msg_urls:
        # 尝试处理第一个链接
        url = msg_urls[0]
        logger.info(f"处理URL: {url}")

        # 尝试检测链接内容类型
        try:
            async with httpx.AsyncClient() as client:
                head_response = await client.head(url, follow_redirects=True)
                content_type = head_response.headers.get("Content-Type", "").lower()
                is_pdf = re.match(pdf_pattern, url) or "application/pdf" in content_type
                logger.info(f"链接内容类型: {content_type} - {head_response.url}")
        except Exception:
            # 如果HEAD请求失败，使用URL后缀判断
            is_pdf = re.match(pdf_pattern, url)

        if is_pdf:
            # 处理PDF链接
            await UniMessage(Text("正在尝试处理PDF文件")).send(reply_to=Reply(msg_id))

            pdf_content = await process_pdf(url)
            if pdf_content:
                user_prompt += f"\n<type: pdf, url: {url}>\n{pdf_content}\n</type: pdf>"
            else:
                return await UniMessage(Text("无法处理PDF文件，请检查文件是否有效且大小合适")).send(reply_to=Reply(msg_id))
        else:
            # 处理普通网页链接
            await UniMessage(Text("正在尝试打开链接")).send(reply_to=Reply(msg_id))

            page_content = await process_web_page(url)
            if page_content:
                user_prompt += f"\n<type: web_page, url: {url}>\n{page_content}\n</type: web_page>"
            else:
                # 最后尝试作为PDF处理
                pdf_content = await process_pdf(url)
                if pdf_content:
                    user_prompt += f"\n<type: pdf, url: {url}>\n{pdf_content}\n</type: pdf>"
                else:
                    return await UniMessage(Text("无法获取页面内容")).send(reply_to=Reply(msg_id))

    # 如果处理了URL/PDF或图片, 更新反应
    if msg_urls or image_list:
        await message_reaction("314", msg_id, event, bot)

    # 准备最终的用户提示
    user_prompt = f"<random number: {random_number}>\n{user_prompt}\n</random number: {random_number}>"
    logger.info(f"最终用户提示: \n{user_prompt}")

    # 生成AI响应
    response = await generate_ai_response(system_prompt, user_prompt)

    if response is None:
        return await UniMessage(Text("AI 回复解析失败, 请重试")).send(reply_to=Reply(msg_id))

    await message_reaction("144", msg_id, event, bot)
    await UniMessage(Text(response)).send(reply_to=reply)
