from importlib.metadata import version

from nonebot import get_driver, get_plugin_config, require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from .browser import install_browser
from .config import Config

require("nonebot_plugin_alconna")


try:
    __version__ = version("nonebot_plugin_zssm")
except Exception:
    __version__ = None


__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-zssm",
    description="这是什么？问一下！用 ai 来解释群友发送的「未知」内容",
    usage="对着任意你不懂的内容发送「zssm」即可",
    homepage="https://github.com/djkcyl/nonebot-plugin-zssm",
    type="application",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={"author": "djkcyl", "version": __version__},
)


config = get_plugin_config(Config)
if config.zssm_install_browser:
    driver = get_driver()
    driver.on_startup(install_browser)

from . import handle  # noqa: E402, F401
