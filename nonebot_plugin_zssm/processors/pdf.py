import tempfile
from io import BytesIO

import fitz  # PyMuPDF
import httpx
from nonebot import get_plugin_config, logger

from ..config import Config

config = get_plugin_config(Config)


async def download_pdf(url: str) -> BytesIO | None:
    """下载PDF文件

    Args:
        url: PDF文件URL

    Returns:
        BytesIO | None: PDF文件的BytesIO对象, 失败时返回None
    """
    try:
        async with httpx.AsyncClient() as client:
            buffer = BytesIO()
            total_size = 0

            async with client.stream("GET", url, timeout=60.0, follow_redirects=True) as response:
                response.raise_for_status()

                async for chunk in response.aiter_bytes():
                    total_size += len(chunk)
                    if total_size > config.zssm_pdf_max_size:
                        logger.error(
                            f"PDF文件过大: {total_size / 1024 / 1024:.2f}MB, 超过{config.zssm_pdf_max_size / 1024 / 1024}MB限制"
                        )
                        return None
                    buffer.write(chunk)

            buffer.seek(0)
            return buffer
    except httpx.HTTPError as e:
        logger.opt(exception=e).error(f"下载PDF失败: {url}, 错误: {e}")
        return None


async def process_pdf(url: str) -> str | None:
    """处理PDF内容

    Args:
        url: PDF文件URL

    Returns:
        Optional[str]: PDF内容文本, 失败时返回None
    """
    try:
        # 下载PDF
        pdf_bytes = await download_pdf(url)
        if not pdf_bytes:
            return None

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            temp_filename = temp_file.name
            temp_file.write(pdf_bytes.getvalue())

            try:
                # 使用PyMuPDF提取文本
                doc = fitz.open(temp_filename)

                # 检查页数
                if len(doc) > config.zssm_pdf_max_pages:
                    logger.info(f"PDF页数过多: {len(doc)}, 将只处理前{config.zssm_pdf_max_pages}页")
                    page_count = config.zssm_pdf_max_pages
                else:
                    page_count = len(doc)

                text_content = []

                # 提取文本
                for page_num in range(page_count):
                    page = doc.load_page(page_num)
                    text_content.append(page.get_textpage().extractText())

                # 拼接所有页面的文本
                full_text = "\n".join(text_content)

                # 如果文本太长，截取前N个字符
                if len(full_text) > config.zssm_pdf_max_chars:
                    logger.info(f"PDF内容过长，已截取前{config.zssm_pdf_max_chars}个字符，原长度: {len(full_text)}")
                    full_text = full_text[: config.zssm_pdf_max_chars] + "\n...[内容过长已截断]"

                return full_text
            finally:
                # 关闭文档并删除临时文件
                if "doc" in locals():
                    doc.close()

    except Exception as e:
        logger.opt(exception=e).error(f"处理PDF失败: {url}, 错误: {e}")
        return None
