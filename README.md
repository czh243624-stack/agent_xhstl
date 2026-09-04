# 小红书研究台

本项目是一个本地运行的小红书研究与发布辅助页面。仓库里已经带好本地运行程序，**不用再单独 git clone 其它仓库**。

## 启动

在项目根目录执行：

```powershell
pip install -r requirements.txt
.\start-page.ps1 -Port 1686
```

打开：

```text
http://127.0.0.1:1686
```

`start-page.ps1` 会先拉起本地服务，再打开页面。第一次启动可能自动下载浏览器内核，需要等几分钟。

## 常用功能

- 扫码登录和检查登录状态
- 搜索笔记、读取笔记详情、查看用户主页
- 发布图文或视频
- 评论、回复、点赞、收藏
- 发布前检测正文风险，并生成改写稿

## 发布图片路径格式

图片参数需要传数组。页面里可以直接逐行填写图片绝对路径，例如：

```text
D:\agent_xhstuiliu\xhs_cover_technical_job_safe.png
```

## 内容检查

发布前检测会读取本地的 `xiaohongshu-content-checker` 规则包。

如需更自然的语义检测和改写，可在启动前配置：

```powershell
$env:OPENAI_API_KEY="你的 API Key"
$env:OPENAI_MODEL="gpt-4o-mini"
.\start-page.ps1 -Port 1686
```

未配置时仍可使用本地规则词表做基础检测和改写。

## 注意

- 本项目只建议本机研究使用。
- 发布、评论、回复、点赞、收藏等操作会影响真实账号，请确认后再执行。
- 登录态保存在本机，不会进 Git。
- 小红书页面结构和风控规则可能变化，自动化能力可能需要后续维护。
