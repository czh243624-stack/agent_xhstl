# xiaohongshu-mcp 研究记录

## 结论

`xiaohongshu-mcp` 是一个非官方的小红书浏览器自动化桥接服务。它在本机启动 Go 程序和 Chromium，通过 Rod 驱动网页端完成登录、检索、读取、发布与互动，再把这些能力同时暴露为 MCP Streamable HTTP 和普通 HTTP API，供 Agent、Claude Code、Cursor、n8n 等客户端调用。

它不是小红书官方开放平台 SDK，也不是直接连接官方公开 API。功能是否稳定依赖小红书网页结构、账号状态、Cookie 有效性和平台风控。

## 本机部署结构

```text
浏览器页面 :1686
      │
      ├─ 自然语言研究入口
      └─ 18 工具 Schema 表单 + 写操作确认
      │
FastAPI 适配层 app.py
      │ MCP initialize / tools/list / tools/call
      ▼
xiaohongshu-mcp :18060/mcp
      │
      ├─ Go 官方 MCP SDK
      ├─ Rod + headless_browser
      ├─ Chromium 网页自动化
      └─ 本地 cookies.json 登录态
      ▼
xiaohongshu.com 网页端
```

当前部署仅监听 `127.0.0.1`，没有直接暴露到局域网或公网。使用的可执行文件为 v2.5.0 发布版；本地源码检出点为提交 `332d196854a9eac0d2b8c2c0e3d0cc43139d724c`。

## 18 个 MCP 工具

| # | 工具 | 用途 | 页面策略 |
|---:|---|---|---|
| 1 | `check_login_status` | 检查登录状态 | 只读，直接执行 |
| 2 | `get_login_qrcode` | 生成扫码登录二维码 | 只读，直接执行 |
| 3 | `delete_cookies` | 删除本地 Cookie、重置登录 | 改变登录状态，二次确认 |
| 4 | `publish_content` | 发布图文、标签、商品及定时内容 | 发布操作，二次确认 |
| 5 | `list_feeds` | 获取首页推荐 Feed | 只读，直接执行 |
| 6 | `search_feeds` | 按关键词和筛选条件搜索 | 只读，直接执行 |
| 7 | `get_feed_detail` | 读取笔记、作者、互动数、评论和视频信息 | 只读，直接执行 |
| 8 | `user_profile` | 查看指定用户的笔记、收藏或点赞页 | 只读，直接执行 |
| 9 | `post_comment_to_feed` | 在笔记下发表评论 | 写操作，二次确认 |
| 10 | `reply_comment_in_feed` | 回复指定评论或用户 | 写操作，二次确认 |
| 11 | `publish_with_video` | 发布本地视频文件 | 发布操作，二次确认 |
| 12 | `like_feed` | 点赞或取消点赞笔记 | 写操作，二次确认 |
| 13 | `favorite_feed` | 收藏或取消收藏笔记 | 写操作，二次确认 |
| 14 | `get_my_profile` | 获取当前登录用户主页 | 只读，直接执行 |
| 15 | `get_unread_count` | 获取三个通知分区的未读数 | 只读，不清未读 |
| 16 | `list_notifications` | 读取评论、赞藏或关注通知 | 会清所选分区未读，二次确认 |
| 17 | `reply_notification` | 直接回复通知里的评论 | 写操作，二次确认 |
| 18 | `like_notification` | 点赞或取消点赞通知里的评论 | 写操作，二次确认 |

工具名称、描述和输入 Schema 由页面启动后通过 `tools/list` 实时读取，不在前端伪造参数。若后续 MCP 升级了字段，工具表单会跟随 Schema 变化。

## 数据与安全边界

- 登录 Cookie 保存在本机运行目录；获取二维码后需要用小红书 App 扫码。
- 同一账号不宜同时在多个网页端登录，否则当前 MCP 登录态可能被顶掉。
- `list_notifications` 虽被上游标记为只读，但源码说明它会清除对应分区的未读标记；本页面因此按有副作用操作处理。
- 发布、评论、回复、点赞、收藏、删除 Cookie 都会改变外部状态，本页面不会从自然语言入口自动执行，必须在工具柜中勾选确认。
- 网页自动化可能随小红书页面改版失效，也可能遇到验证码、实名认证、频率限制或账号风控。
- 若要允许其他设备访问，应先启用项目的 `AUTH_TOKEN` 鉴权并通过受控反向代理部署；不要直接把无鉴权的 `18060` 端口暴露公网。

## 源码证据

- `xiaohongshu-mcp/mcp_server.go`：18 个工具、参数结构和风险注解。
- `xiaohongshu-mcp/service.go`：浏览器生命周期、扫码登录与 Cookie 保存。
- `xiaohongshu-mcp/go.mod`：Rod、stealth 和 headless_browser 依赖。
- `xiaohongshu-mcp/docs/API.md`：HTTP API 与 MCP 双协议说明。
- `xiaohongshu-mcp/README.md`：部署、登录、客户端接入及项目风险提示。
- `xiaohongshu-mcp/LICENSE`：Apache License 2.0。
