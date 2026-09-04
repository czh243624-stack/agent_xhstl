---
name: 小红书研究台
description: 一张把真实 MCP 返回采集、标记并归档的野外样本台。
colors:
  carbon-ink: "#141412"
  raised-carbon: "#292925"
  evidence-paper: "#f2efdf"
  aged-paper: "#dfdccb"
  acid-index: "#d8ff3e"
  vermilion-note: "#ff5a36"
  field-muted: "#7e7b70"
  graphite-worktop: "#5b5a52"
  hairline: "rgba(20, 20, 18, 0.18)"
typography:
  display:
    fontFamily: '"Field Serif SC", "SimSun", serif'
    fontSize: "clamp(34px, 5vw, 68px)"
    fontWeight: 900
    lineHeight: 0.98
    letterSpacing: "-0.035em"
  headline:
    fontFamily: '"Field Serif SC", "SimSun", serif'
    fontSize: "clamp(30px, 4.4vw, 58px)"
    fontWeight: 900
    lineHeight: 1.05
    letterSpacing: "-0.035em"
  title:
    fontFamily: '"Field Serif SC", "SimSun", serif'
    fontSize: "17px"
    fontWeight: 900
  body:
    fontFamily: '"Microsoft YaHei UI", "Microsoft YaHei", sans-serif'
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.78
  label:
    fontFamily: '"Bahnschrift", sans-serif'
    fontSize: "10px"
    fontWeight: 650
    lineHeight: 1
    letterSpacing: "0.08em"
  control:
    fontFamily: '"Microsoft YaHei UI", "Microsoft YaHei", sans-serif'
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  action:
    fontFamily: '"Microsoft YaHei UI", "Microsoft YaHei", sans-serif'
    fontSize: "16px"
    fontWeight: 800
  microcopy:
    fontFamily: '"Microsoft YaHei UI", "Microsoft YaHei", sans-serif'
    fontSize: "10px"
    fontWeight: 400
  mono:
    fontFamily: '"Consolas", monospace'
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  tag: "4px"
  soft: "8px"
  field: "10px"
  container: "14px"
  specimen: "4px 10px 8px 5px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "20px"
  xl: "28px"
  xxl: "40px"
components:
  primary-action:
    backgroundColor: "{colors.acid-index}"
    textColor: "{colors.carbon-ink}"
    typography: "{typography.action}"
    rounded: "{rounded.field}"
    padding: "0 18px"
    width: "126px"
    height: "68px"
  specimen-action:
    backgroundColor: "{colors.carbon-ink}"
    textColor: "{colors.evidence-paper}"
    rounded: "{rounded.soft}"
    padding: "11px 17px"
  task-field:
    backgroundColor: "{colors.carbon-ink}"
    textColor: "{colors.evidence-paper}"
    typography: "{typography.control}"
    rounded: "{rounded.field}"
    padding: "13px 14px"
    height: "68px"
  suggestion-chip:
    backgroundColor: "transparent"
    textColor: "{colors.field-muted}"
    typography: "{typography.microcopy}"
    rounded: "{rounded.pill}"
    padding: "5px 9px"
  specimen-sheet:
    backgroundColor: "{colors.evidence-paper}"
    textColor: "{colors.carbon-ink}"
    rounded: "{rounded.specimen}"
    padding: "clamp(28px, 4vw, 58px)"
---

# Design System: 小红书研究台

## Overview

**Creative North Star: “野外样本台”**

“野外样本台”把研究会话当成真实证物的采集、标记与归档，而不是通用聊天应用的气泡流。炭黑工作面围住米白样本纸，酸性黄绿承担索引与活动信号，朱红只用于批注、失败和扫描提示；整体密度偏高，但依靠强烈的明暗分区保持清晰。

界面组件应像标签、抽屉、样本夹和盖章，而不是柔软的消费级卡片。展示字体通过本地字面解析，保证离线工作台仍有可靠的宋体展示声调；所有交互继续强调这是一个只读研究表面，真实 MCP 返回是视觉中心。该方向是在未收到用户选择后依授权委派，并由已交付页面固化为当前设计基线。

**Key Characteristics:**

- 深色设备台面与暖米白证物纸形成明确的工作区分层。
- 酸性黄绿负责主操作、状态和索引，出现频率低但辨识度高。
- 朱红是批注色，始终搭配深色墨字以维持对比。
- 紧凑无衬线信息层与大幅本地宋体标题并置。
- 轻微旋转、不规则圆角和夹具轮廓制造手工归档感。

## Colors

色彩像一张在暗色采集台上摊开的旧纸记录：中性层承担大面积结构，两种高能量色只负责索引和批注。

### Primary

- **酸性索引** (`colors.acid-index`): 用于主采集按钮、在线与完成状态、计数、样本编号和焦点轮廓；它是行动与“已确认”的单一视觉信号。

### Secondary

- **朱红批注** (`colors.vermilion-note`): 用于失败状态、扫描进度和只读封条；作为底色时必须使用炭黑文字。

### Neutral

- **炭黑墨面** (`colors.carbon-ink`): 页面底色、侧栏和纸面文字的主基准。
- **抬升炭面** (`colors.raised-carbon`): 顶部任务输入容器，和页面底色形成轻微层级。
- **证物纸** (`colors.evidence-paper`): 主要结果与空状态的承载面，也用作暗色区域上的主文字色。
- **旧纸背面** (`colors.aged-paper`): 加载轨道和纸面内部的次级层。
- **石墨工作台** (`colors.graphite-worktop`): 中央桌面底色，用来托起证物纸。
- **现场灰** (`colors.field-muted`): 非活动轨迹、说明和弱标签。
- **墨色发丝线** (`colors.hairline`): 纸面数据分隔，不承担容器装饰。

**The Two-Marker Rule.** 酸性索引只表示行动、活动或确认；朱红批注只表示扫描、异常或封条，二者不可互换。

## Typography

**Display Font:** Field Serif SC（本地 Noto Serif SC、SimSun 或宋体字面）  
**Body Font:** Microsoft YaHei UI（Microsoft YaHei 与系统无衬线后备）  
**Label/Mono Font:** Bahnschrift 用于仪器标签，Consolas 用于原始数据

**Character:** 展示层厚重、窄距、近乎海报式；操作与说明层克制而清晰。英文仪器标签以 Bahnschrift 的小字号、半粗体和扩展字距建立样本编号感，原始数据则保持等宽。

### Hierarchy

- **Display**（900，`clamp(34px, 5vw, 68px)`，0.98）: 空状态的唯一主标题，允许极紧行高与负字距。
- **Headline**（900，`clamp(30px, 4.4vw, 58px)`，1.05）: MCP 返回结果标题，控制在约 16 个汉字宽以内。
- **Title**（700，17px）: 品牌名与少量功能标题，不与展示标题竞争。
- **Body**（400，14px，1.78）: 结果说明与长文本；正文以 58–72ch 为宜，避免铺满纸张。
- **Label**（650，10px，0.08em）: 全大写英文状态、编号和设备提示。
- **Mono**（400，11px，1.6）: 展开的结构化原始数据。

**The Offline Display Rule.** 展示字体必须先尝试本地 Noto Serif SC，再回退到 SimSun/宋体；不得让网络字体成为页面可读或成形的前提。

## Layout

桌面端采用不对称三栏工作台：左侧索引为 252px，中间工作区至少 420px 并弹性扩展，右侧行动轨迹为 316px；76px 高的顶栏横跨全宽。中央命令条和样本纸共享 1060px 最大宽度，桌面内边距横向在 20–46px 间流动，纸张内边距在 28–58px 间流动。

在 1120px 及以下，右侧轨迹移到整行底部并改为三列；在 760px 及以下，整个工作区变为单列，索引动作改为两列，历史与范围说明收起，命令输入和主操作纵向堆叠；430px 以下进一步压缩品牌与系统状态。间距以 4px 为细节单位，常用节拍集中在 8、12、20、28 和 40px。

## Elevation & Depth

系统使用“平面设备 + 浮起证物”的混合深度。侧栏、导航和轨迹默认无阴影，靠色块与细分隔线组织；只有命令条和样本纸使用宽而柔的环境阴影，结果图片使用更小的纸片阴影，主按钮仅在悬停时短暂抬升。

### Shadow Vocabulary

- **证物浮影** (`0 18px 55px rgba(0, 0, 0, 0.28)`): 命令条与样本纸的共享阴影，表现它们放在工作台上方。
- **操作荧光** (`0 8px 22px rgba(216, 255, 62, 0.20)`): 仅在主采集按钮悬停时出现，配合向上 2px 位移。
- **图片纸片** (`0 12px 28px rgba(20, 20, 18, 0.17)`): 结果图片的局部抬升，必须与白色实物边框同时出现。

**The Evidence Float Rule.** 阴影只证明某件东西被放到台面上；侧栏、列表行和普通标签保持平面。

## Shapes

形状语言以工具性的直边为基础，再在“被拿取的物件”上加入轻微不规则。命令容器使用 14px 柔角，输入和主按钮使用 10px，普通操作使用 8px，元数据标签使用 4px；样本纸采用不对称的 `4px 10px 8px 5px` 纸角。圆形、椭圆和轻微旋转只用于品牌印记、轨迹节点、夹具、封条与抽象样本图形。胶囊形只属于建议词，不扩散为默认按钮形态。

## Components

### Buttons

- **Shape:** 主采集按钮采用紧凑柔角（10px）；纸面次操作采用较小柔角（8px）；索引动作保持直边并由分隔线划分。
- **Primary:** 酸性索引底配炭黑字，桌面端固定 126px 宽并与最小 68px 的输入等高；字重 800。
- **Hover / Focus:** 主按钮在 180ms 内上移 2px 并出现操作荧光；所有按钮、输入与链接使用 3px 酸性索引焦点轮廓和 3px 外偏移。
- **Secondary:** 纸面操作为炭黑底、证物纸文字和 8px 圆角；索引动作悬停时整行反转为酸性索引底和炭黑字。

### Chips

- **Style:** 建议词为透明底、1px 低对比纸色边框、胶囊轮廓（999px）与 5px × 9px 内边距。
- **State:** 默认弱化；悬停只提亮文字和边框，不填充。结果元数据不是可点击 chip，而是 4px 圆角的酸性索引标签。

### Cards / Containers

- **Corner Style:** 命令条为 14px；样本纸使用不对称纸角。
- **Background:** 命令条使用抬升炭面，样本纸使用证物纸，中央底层保持石墨工作台。
- **Shadow Strategy:** 只有命令条、样本纸和结果图片遵循“证物浮影”。
- **Border:** 侧栏与列表使用低对比细线或虚线；样本纸本身无描边。
- **Internal Padding:** 命令条为 14px 16px 12px；样本纸为响应式 28–58px。

### Inputs / Fields

- **Style:** 任务文本框为炭黑底、证物纸文字、1px 半透明纸色描边和 10px 圆角；内边距 13px 14px，最小高度 68px。
- **Focus:** 使用全局 3px 酸性索引外轮廓，不以阴影替代键盘焦点。
- **Disabled:** 输入与主按钮在任务执行期间同时禁用；主按钮降低到 55% 不透明度并取消位移和阴影。

### Navigation

左侧索引由编号和动作名组成，行高紧凑、整行可点击；默认透明底配纸色文字，悬停整行切换为酸性索引。移动端索引改为两列有框按钮，编号移到文字上方，历史记录从首屏收起。

### Specimen Sheet

样本纸是系统的签名组件：它同时承载空状态、加载、失败和真实结果，并通过顶部夹具、右上角现场注记和右下角倾斜朱红封条建立“证物”语义。朱红封条必须使用炭黑文字。结果揭示使用 440ms 的自上而下裁切动画；加载扫描线为朱红，遇到 `prefers-reduced-motion` 时取消所有扫描与揭示动画。

### Agent Trace

轨迹使用一条 1px 垂直线串联 11px 节点：完成节点填充酸性索引，活动节点使用朱红描边与低透明外环，未开始节点保持现场灰。它是过程记录，不使用聊天头像、消息气泡或对话尾巴。

## Do's and Don'ts

### Do:

- **Do** 保持深色工作台围住一张主要证物纸，让真实返回始终成为最大、最亮的表面。
- **Do** 让酸性索引只服务于主操作、活动状态、确认与编号。
- **Do** 在朱红标签和封条上使用炭黑文字，维持高对比和印章感。
- **Do** 保留本地展示字体后备、清晰焦点轮廓和减弱动态模式。

### Don't:

- **Don't** 把研究过程改成普通聊天气泡、消息卡流或对话尾巴。
- **Don't** 给每个区域都加圆角和阴影；侧栏与列表应保持平面、克制。
- **Don't** 用通用纯白仪表盘替代暖纸、石墨工作台和炭黑设备面。
- **Don't** 大面积铺设酸性索引或朱红，也不要在朱红底上使用浅色文字。
