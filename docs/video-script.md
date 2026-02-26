# AI Site Builder 产品演示视频脚本

> **视频规格**：37 秒 | 1920×1080 | 30fps  
> **目标受众**：需要快速搭建网站的企业用户、创业者、个人开发者  
> **视频风格**：科技感、简洁、专业

---

## 分镜总览

| 分镜 | 时长 | 帧数 | 场景名称 | 核心内容 |
|------|------|------|----------|----------|
| 1 | 0:00-0:05 | 0-150 | 开场 Hook | 引发兴趣，提出更简单的方式 |
| 2 | 0:05-0:20 | 150-600 | AI 对话收集 | 完整 4 步流程：对话 + 选项 + 确认 |
| 3 | 0:20-0:26 | 600-780 | AI 生成 | 生成过程动画（快速） |
| 4 | 0:26-0:32 | 780-960 | 成果展示 | 生成的网页效果（6页面） |
| 5 | 0:32-0:37 | 960-1110 | 结尾 CTA | 行动号召 |

---

## 分镜 1：开场 Hook（5 秒）

### 画面内容
- **背景**：浅色渐变背景 `#f7f8fa` -> `#f6f2ff`，带微光效果
- **主视觉**：
  - 中心大字："想做一个网站？"
  - 下方副标题渐显："现在有更简单的方式"
  - 周围漂浮着网站相关的抽象图标（代码块、布局框、图片占位符）
- **动画效果**：
  - 0-60帧：主标题从中心放大淡入
  - 60-120帧：副标题从下方滑入
  - 0-150帧：背景图标缓慢漂浮移动

### 口播脚本
> **中文**：「想做一个网站？现在有更简单的方式」  
> **English**："Want to build a website? There's an easier way now"

### 技术备注
- 主标题使用 `style.gradientText` 渐变文字
- 漂浮图标使用 `Math.sin()` 实现轻微浮动效果
- 整体氛围：轻松、期待感

---

## 分镜 2：AI 对话收集需求（15 秒）

### 画面内容
- **背景**：浅色背景 `#f7f8fa`
- **主视觉**：模拟产品界面（左侧对话区 + 右侧信息卡片）
- **动画分段**：

**阶段 A：界面入场 + 步骤 1（0-4秒，150-270帧）**
- 150-180帧：产品界面从底部整体滑入
- 顶部显示 4 步进度条，步骤 1「Business Type」高亮
- 180-210帧：AI 消息气泡出现："请问你想做什么类型的网站？"
- 210-240帧：选项卡片网格出现（企业官网、电商、博客、教育课程...）
- 240-270帧："教育课程" 被选中，进度条步骤 1 打勾 ✓

**阶段 B：步骤 2 - 功能模块（4-7秒，270-360帧）**
- 进度条步骤 2「Service Items」高亮
- 270-300帧：AI 提问："需要哪些功能模块？"
- 300-330帧：多选卡片出现（在线课程、预约系统、作品展示...）
- 330-360帧：多个选项被勾选，步骤 2 打勾 ✓

**阶段 C：步骤 3 - 网站信息（7-10秒，360-450帧）**
- 进度条步骤 3「Website Info」高亮
- 360-390帧：AI 提问："网站名称是什么？"
- 390-420帧：用户输入 "智学在线教育"
- 420-450帧：右侧卡片更新显示网站名称，步骤 3 打勾 ✓

**阶段 D：步骤 4 + 确认（10-15秒，450-600帧）**
- 进度条步骤 4「Goals」高亮
- 450-480帧：AI 提问："网站的商业目标是？"
- 480-510帧：目标选项出现（品牌曝光、获客转化、增加订单...）
- 510-540帧：选项被选中，步骤 4 打勾 ✓，全部完成
- 540-570帧：AI 消息 "信息收集完成，确认提交？"
- 570-600帧：确认按钮被点击，右侧卡片显示完整信息

### 口播脚本
> **中文**：「和 AI 对话，选择业务类型、功能模块、填写信息、设定目标，4 步完成需求收集」  
> **English**："Chat with AI — business type, features, info, goals — 4 steps to complete"

### 技术备注
- 打字机效果：`interpolate(frame, [start, end], [0, text.length])`
- 选项卡片使用 `springConfig.bouncy` 弹性入场
- 进度条每步完成后显示渐变勾选动画
- 右侧信息卡片实时更新，体现"同步收集"

---

## 分镜 3：AI 生成动画（6 秒）

### 画面内容
- **背景**：深色科技感背景 `#1a1a2e` -> `#0f3460`，带网格线
- **主视觉**：
  - 中心：大型 AI 图标，带旋转光环
  - 周围：漂浮的代码片段、粒子效果
  - 进度条 + 状态文字
- **动画效果**：
  - 600-630帧：场景切换，深色背景淡入，AI 图标放大出现
  - 630-660帧：光环开始旋转，状态显示 "正在生成..."
  - 660-720帧：进度条快速推进 0% → 100%
  - 720-780帧：完成动画，显示 "生成完成！"

### 口播脚本
> **中文**：「AI 智能生成，几秒钟搞定」  
> **English**："AI generates instantly — done in seconds"

### 技术备注
- 光环旋转：`interpolate(frame, [0, fps*2], [0, 360])`
- 进度条快速填充，体现"高效"
- 粒子效果：8 个粒子环绕运动

---

## 分镜 4：成果展示（6 秒）

### 画面内容
- **背景**：浅色渐变，带微光效果
- **主视觉**：
  - 展示 AI 生成的网页效果图（6 个页面，2x3 网格）
  - 页面类型：首页、课程、价格、关于、联系、博客
  - 带浏览器框架装饰，PC 端宽屏布局
  - 首页居中突出显示（蓝色边框）
- **动画效果**：
  - 780-800帧：标题滑入
  - 800-960帧：6 个网页卡片依次弹入，轻微浮动

### 口播脚本
> **中文**：「专业网页即刻生成」  
> **English**："Professional pages generated instantly"

### 技术备注
- 标题使用渐变文字 `designStyle.gradientText`
- 网页卡片使用 2x3 网格布局，尺寸 400x250
- 首页卡片带主色边框和更强阴影突出显示

---

## 分镜 5：结尾 CTA（5 秒）

### 画面内容
- **背景**：渐变背景，带装饰性光晕
- **主视觉**：
  - 主标题："开始创建你的网站"
  - 副标题："AI Site Builder - 让创意变为现实"
  - CTA 按钮："立即体验"（带脉冲动画）
  - 底部标签：对话式交互 | AI 智能生成 | 快速上线
- **动画效果**：
  - 1020-1050帧：标题从上方滑入
  - 1050-1080帧：副标题淡入
  - 1080-1140帧：CTA 按钮弹入，开始脉冲动画
  - 1140-1170帧：底部标签依次出现

### 口播脚本
> **中文**：「AI Site Builder，让创意变为现实。立即体验！」  
> **English**："AI Site Builder — turn ideas into reality. Try it now!"

### 技术备注
- CTA 按钮脉冲：`1 + Math.sin(frame * 0.15) * 0.03`
- 渐变文字：`style.gradientText`
- 底部标签间距 40px

---

## 完整口播脚本

### 中文版（约 37 秒）

```
[0:00-0:05] 想做一个网站？现在有更简单的方式。

[0:05-0:20] 和 AI 对话，选择业务类型、功能模块、填写信息、设定目标，4 步完成需求收集。

[0:20-0:26] AI 智能生成，几秒钟搞定。

[0:26-0:32] 专业网页即刻生成。

[0:32-0:37] AI Site Builder，让创意变为现实。立即体验！
```

### English Version (~37 seconds)

```
[0:00-0:05] Want to build a website? There's an easier way now.

[0:05-0:20] Chat with AI — business type, features, info, goals — 4 steps to complete.

[0:20-0:26] AI generates instantly — done in seconds.

[0:26-0:32] Professional pages generated instantly.

[0:32-0:37] AI Site Builder — turn ideas into reality. Try it now!
```

---

## 视觉风格参考

> 完整设计系统定义见 [design-system.ts](./design-system.ts)

### 配色方案（colors）
- 主色：`colors.primary` (#3b91ff)
- 深主色：`colors.primaryDark` (#0d5eff)
- 强调色：`colors.accent` (#c069ff)
- 渐变：`colors.gradient` / `colors.gradientHorizontal`
- 浅色背景：`colors.bgLight` (#f7f8fa) / `colors.bgLightAlt` (#f6f2ff)
- 深色背景：`colors.bgDark` (#0a0a1a) / `colors.bgDarkAlt` (#1a1a3e)
- 成功色：`colors.success` (#52c41a)
- 文字色：`colors.textPrimary` / `colors.textSecondary` / `colors.textMuted`

### 动画配置（springConfig）
- 柔和入场：`springConfig.gentle` - 适用于大元素、标题
- 弹性强调：`springConfig.bouncy` - 适用于按钮、图标、卡片入场
- 快速响应：`springConfig.snappy` - 适用于小元素、过渡
- 超快：`springConfig.quick` - 适用于微交互

### 字体规范（font）
- 大标题：`font.h1` (72px, 700)
- 副标题：`font.h2` / `font.h3` (56px / 42px)
- 正文：`font.body` (20px, 400)
- 小字：`font.small` (16px, 400)
- 标签：`font.label` (14px, 500)

### 组件样式（components）
- AI 头像：`components.aiAvatar(size)`
- AI 气泡：`components.aiBubble`
- 用户气泡：`components.userBubble`
- 选项卡片：`components.optionCard` / `components.optionCardActive`
- 步骤指示器：`components.stepIndicator(size)` / `components.stepIndicatorActive(size)`
- CTA 按钮：`components.ctaButton`
- 浏览器框架：`components.browserFrame`

### 通用样式（style）
- 渐变文字：`style.gradientText`
- 居中：`style.center`
- 白色卡片：`style.card`
- 毛玻璃卡片：`style.glassCard`
- 浅色场景背景：`style.bgSceneLight`
- 深色场景背景：`style.bgSceneDark`

### 工具函数
- 背景光晕：`createGlow('primary' | 'accent' | 'success', opacity, size)`
- 网格背景：`createGrid(color, size)`

---

## 音效建议

| 时间点 | 音效类型 | 说明 |
|--------|----------|------|
| 0:00 | 背景音乐开始 | 轻快科技感 BGM |
| 0:03 | 文字出现音效 | 轻微的弹出提示音 |
| 0:05 | 界面入场音效 | 轻微滑动音 |
| 0:09 | 选中音效 | 步骤 1 完成 |
| 0:12 | 选中音效 | 步骤 2 完成 |
| 0:15 | 选中音效 | 步骤 3 完成 |
| 0:18 | 确认音效 | 步骤 4 完成 + 提交 |
| 0:20 | 启动音效 | AI 开始工作 |
| 0:26 | 成功音效 | 叮咚提示音 |
| 0:34 | 高潮音效 | 配合 CTA 出现 |

---

## Remotion 实现清单

- [ ] 创建 `HookScene.tsx` - 开场引导场景
- [ ] 创建 `ChatCollectScene.tsx` - AI 对话收集需求场景（完整 4 步流程）
- [ ] 更新 `AIGenerateScene.tsx` - 调整为 6 秒快速版
- [ ] 创建 `ResultScene.tsx` - 成果展示场景
- [ ] 更新 `OutroScene.tsx` - 优化 CTA 动画
- [ ] 更新 `DemoVideo.tsx` - 调整为 5 个场景，总时长 39 秒
