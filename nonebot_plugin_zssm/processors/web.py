from nonebot import get_plugin_config, logger
from yarl import URL

from ..browser import get_browser
from ..config import Config

config = get_plugin_config(Config)


async def process_web_page(url: str) -> str | None:
    """处理网页内容

    Args:
        url: 网页URL

    Returns:
        Optional[str]: 网页内容, 失败时返回None
    """
    try:
        if config.zssm_browser_proxy:
            proxy_uri = URL(config.zssm_browser_proxy)
            proxy = {
                "server": f"{proxy_uri.scheme}://{proxy_uri.host}:{proxy_uri.port}",
                "username": proxy_uri.user,
                "password": proxy_uri.password,
            }
        else:
            proxy = None

        logger.info(f"使用代理: {proxy}，{config.zssm_browser_proxy}")
        browser = await get_browser(proxy=proxy)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=60000)
        except Exception as e:
            logger.opt(exception=e).error(f"打开链接失败: {url}, 错误: {e}")
            await page.close()
            return None

        # 获取页面的内容
        page_content = await page.query_selector("html")
        content_text = None

        if page_content:
            content_text = await page_content.inner_text()

        await page.close()

    except Exception as e:
        logger.opt(exception=e).error(f"处理网页失败: {url}, 错误: {e}")
        return None
    else:
        return content_text
