<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-zssm

_✨ 这是什么？问一下！ ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/owner/nonebot-plugin-zssm.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-zssm">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-zssm.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="python">

</div>

## 📖 介绍

这是一个 nonebot2 的 ai 解释插件，对着你想要了解的东西，回复「zssm」吧！

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-zssm

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-zssm
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-zssm
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-zssm
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-zssm
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_zssm"]

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| zssm_ai_text_endpoint | 否 | https://api.deepseek.com/v1 | 解释使用的 ai 端点 |
| zssm_ai_text_token | 是 | 无 | 解释使用的 api-key |
| zssm_ai_text_model | 否 | deepseek-reasoner | 解释使用的模型 |
| zssm_ai_vl_endpoint | 否 | https://api.siliconflow.cn/v1 | 识图使用的 ai 端点 |
| zssm_ai_vl_token | 是 | 无 | 解释使用的 api-key |
| zssm_ai_vl_model | 否 | Qwen/Qwen2.5-VL-72B-Instruct | 解释使用的模型 |
| zssm_ai_check_endpoint | 否 | https://api.deepseek.com/v1 | 审查使用的 ai 端点 |
| zssm_ai_check_token | 否 | 无 | 审查使用的 api-key，不填则不进行审查 |
| zssm_ai_check_model | 否 | deepseek-v3 | 审查使用的模型 |
| zssm_browser_proxy | 否 | 无 | 浏览器代理 |
| zssm_install_browser | 否 | True | 启动时安装浏览器 |
| zssm_pdf_max_size | 否 | 10 | 最大pdf大小 |
| zssm_pdf_max_chars | 否 | 300000 | 最大字符数 |
| zssm_pdf_max_pages | 否 | 50 | 最大页数 |

## 🎉 使用
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| zssm | 无 | 否 | 回复 | 对着需要解释的东西回复一下 |

### 效果图

![05f21be5fdf0221fe8f13e64342ed622](https://github.com/user-attachments/assets/68e806b6-895e-41dd-a08e-303b1a2abcb3)

![8ef4fdfcf05161dcaf77a27cab1670b5](https://github.com/user-attachments/assets/496b26e3-3f93-4db1-8687-88a0637122ff)

