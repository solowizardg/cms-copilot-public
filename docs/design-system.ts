/**
 * AI Site Builder 视频设计系统
 * 统一配色、字体、动画和组件样式规范
 */
import type { CSSProperties } from 'react';

// ============================================
// 🎨 配色系统
// ============================================
export const colors = {
  // 主色 - 科技蓝紫渐变
  primary: '#3b91ff',
  primaryDark: '#0d5eff',
  accent: '#c069ff',

  // 渐变
  gradient: 'linear-gradient(135deg, #3b91ff 0%, #0d5eff 50%, #c069ff 100%)',
  gradientHorizontal: 'linear-gradient(90deg, #3b91ff 0%, #0d5eff 43%, #c069ff 100%)',
  gradientVertical: 'linear-gradient(180deg, #3b91ff 0%, #c069ff 100%)',
  gradientRadial: 'radial-gradient(circle, #3b91ff 0%, #c069ff 100%)',

  // 浅色背景
  bgLight: '#f7f8fa',
  bgLightAlt: '#f6f2ff',
  bgLightGray: '#f9f9f9',
  bgMediumGray: '#f5f5f5',
  bgCard: '#ffffff',
  bgGlass: 'rgba(255, 255, 255, 0.85)',

  // 深色背景
  bgDark: '#0a0a1a',
  bgDarkAlt: '#1a1a3e',
  bgDarkDeep: '#0f3460',
  bgGlassDark: 'rgba(26, 26, 46, 0.9)',

  // 文字
  textPrimary: '#1d2129',
  textSecondary: 'rgba(0, 0, 0, 0.65)',
  textMuted: 'rgba(0, 0, 0, 0.45)',
  textLight: '#ffffff',
  textLightMuted: 'rgba(255, 255, 255, 0.7)',

  // 状态色
  success: '#52c41a',
  successLight: '#73d13d',
  warning: '#faad14',
  error: '#ff4d4f',

  // 边框
  border: 'rgba(0, 0, 0, 0.08)',
  borderLight: 'rgba(255, 255, 255, 0.3)',
  borderActive: '#3b91ff',

  // 透明色（用于光效）
  primaryAlpha: (alpha: number) => `rgba(59, 145, 255, ${alpha})`,
  accentAlpha: (alpha: number) => `rgba(192, 105, 255, ${alpha})`,
  successAlpha: (alpha: number) => `rgba(82, 196, 26, ${alpha})`,
};

// ============================================
// 📐 间距 & 圆角
// ============================================
export const spacing = {
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 64,
};

export const radius = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  full: 9999,
};

// ============================================
// 🔤 字体规范
// ============================================
export const font = {
  // 标题
  h1: { fontSize: 72, fontWeight: 700 as const, lineHeight: 1.2 },
  h2: { fontSize: 56, fontWeight: 700 as const, lineHeight: 1.2 },
  h3: { fontSize: 42, fontWeight: 600 as const, lineHeight: 1.3 },
  h4: { fontSize: 32, fontWeight: 600 as const, lineHeight: 1.3 },

  // 正文
  body: { fontSize: 20, fontWeight: 400 as const, lineHeight: 1.6 },
  bodyLarge: { fontSize: 24, fontWeight: 400 as const, lineHeight: 1.6 },
  small: { fontSize: 16, fontWeight: 400 as const, lineHeight: 1.5 },
  tiny: { fontSize: 12, fontWeight: 400 as const, lineHeight: 1.5 },

  // 标签
  label: { fontSize: 14, fontWeight: 500 as const, letterSpacing: '0.02em' },

  // 代码
  code: { fontSize: 14, fontWeight: 400 as const, fontFamily: 'monospace' },
};

// ============================================
// 🌫️ 阴影
// ============================================
export const shadow = {
  // 基础阴影
  sm: '0 2px 8px rgba(0, 0, 0, 0.06)',
  md: '0 4px 20px rgba(0, 0, 0, 0.08)',
  lg: '0 12px 40px rgba(0, 0, 0, 0.12)',
  xl: '0 20px 60px rgba(0, 0, 0, 0.15)',

  // 主色阴影
  primary: '0 12px 40px rgba(59, 145, 255, 0.25)',
  primaryStrong: '0 20px 60px rgba(59, 145, 255, 0.35)',
  accent: '0 12px 40px rgba(192, 105, 255, 0.25)',
  success: '0 12px 40px rgba(82, 196, 26, 0.25)',

  // 发光效果
  glow: '0 0 40px rgba(59, 145, 255, 0.4)',
  glowAccent: '0 0 40px rgba(192, 105, 255, 0.4)',
  glowSuccess: '0 0 40px rgba(82, 196, 26, 0.4)',

  // 内阴影
  inner: 'inset 0 2px 4px rgba(0, 0, 0, 0.06)',
};

// ============================================
// ✨ 通用样式
// ============================================
export const style = {
  // 渐变文字
  gradientText: {
    background: colors.gradientHorizontal,
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  } as CSSProperties,

  // 居中
  center: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  } as CSSProperties,

  // 绝对居中
  absoluteCenter: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
  } as CSSProperties,

  // 白色卡片
  card: {
    background: colors.bgCard,
    borderRadius: radius.xl,
    boxShadow: shadow.md,
    border: `1px solid ${colors.border}`,
  } as CSSProperties,

  // 毛玻璃卡片
  glassCard: {
    background: colors.bgGlass,
    backdropFilter: 'blur(20px)',
    borderRadius: radius.xl,
    border: `1px solid ${colors.borderLight}`,
    boxShadow: shadow.md,
  } as CSSProperties,

  // 暗色毛玻璃
  glassCardDark: {
    background: colors.bgGlassDark,
    backdropFilter: 'blur(20px)',
    borderRadius: radius.xl,
    border: '1px solid rgba(255, 255, 255, 0.1)',
  } as CSSProperties,

  // 浅色场景背景
  bgSceneLight: {
    background: `linear-gradient(180deg, ${colors.bgLight} 0%, ${colors.bgLightAlt} 100%)`,
  } as CSSProperties,

  // 深色场景背景
  bgSceneDark: {
    background: `linear-gradient(135deg, ${colors.bgDark} 0%, ${colors.bgDarkAlt} 50%, ${colors.bgDarkDeep} 100%)`,
  } as CSSProperties,
};

// ============================================
// 🎬 动画配置 (Remotion spring)
// ============================================
export const springConfig = {
  // 柔和入场 - 适用于大元素、标题
  gentle: { damping: 200, stiffness: 100 },

  // 弹性强调 - 适用于按钮、图标、卡片入场
  bouncy: { damping: 15, stiffness: 80 },

  // 快速响应 - 适用于小元素、过渡
  snappy: { damping: 25, stiffness: 150 },

  // 超快 - 适用于微交互
  quick: { damping: 30, stiffness: 200 },
};

// ============================================
// 🧩 组件样式
// ============================================
export const components = {
  // AI 头像
  aiAvatar: (size: number = 48): CSSProperties => ({
    width: size,
    height: size,
    borderRadius: size / 2,
    background: colors.gradient,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: shadow.primary,
    flexShrink: 0,
  }),

  // 用户头像
  userAvatar: (size: number = 48): CSSProperties => ({
    width: size,
    height: size,
    borderRadius: size / 2,
    background: colors.bgLight,
    border: `2px solid ${colors.border}`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  }),

  // AI 消息气泡
  aiBubble: {
    background: colors.bgLightAlt,
    borderRadius: radius.lg,
    borderTopLeftRadius: radius.xs,
    padding: '18px 24px',
  } as CSSProperties,

  // 用户消息气泡
  userBubble: {
    background: colors.primary,
    borderRadius: radius.lg,
    borderTopRightRadius: radius.xs,
    padding: '18px 24px',
  } as CSSProperties,

  // 选项卡片（未选中）
  optionCard: {
    background: colors.bgCard,
    borderRadius: radius.md,
    border: `1px solid ${colors.border}`,
    padding: spacing.md,
    cursor: 'pointer',
    transition: 'all 0.2s',
  } as CSSProperties,

  // 选项卡片（选中）
  optionCardActive: {
    background: colors.bgCard,
    borderRadius: radius.md,
    border: `2px solid ${colors.primary}`,
    padding: spacing.md,
    boxShadow: shadow.primary,
  } as CSSProperties,

  // 进度条容器
  progressBar: {
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: radius.sm,
    overflow: 'hidden',
  } as CSSProperties,

  // 进度条填充
  progressFill: {
    height: '100%',
    background: colors.gradient,
    borderRadius: radius.sm,
    transition: 'width 0.3s',
  } as CSSProperties,

  // 步骤指示器（未完成）
  stepIndicator: (size: number = 56): CSSProperties => ({
    width: size,
    height: size,
    borderRadius: size / 2,
    background: colors.bgLightAlt,
    border: `2px solid ${colors.border}`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  }),

  // 步骤指示器（进行中）
  stepIndicatorActive: (size: number = 56): CSSProperties => ({
    width: size,
    height: size,
    borderRadius: size / 2,
    background: colors.gradient,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: shadow.primary,
  }),

  // 步骤指示器（已完成）
  stepIndicatorDone: (size: number = 56): CSSProperties => ({
    width: size,
    height: size,
    borderRadius: size / 2,
    background: colors.gradient,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  }),

  // CTA 按钮
  ctaButton: {
    padding: '20px 60px',
    background: colors.gradient,
    borderRadius: radius.lg,
    boxShadow: shadow.primaryStrong,
    border: 'none',
    cursor: 'pointer',
  } as CSSProperties,

  // 输入框
  input: {
    background: colors.bgCard,
    border: `1px solid ${colors.border}`,
    borderRadius: radius.lg,
    padding: '18px 24px',
    boxShadow: shadow.sm,
  } as CSSProperties,

  // 输入框（激活）
  inputActive: {
    background: colors.bgCard,
    border: `2px solid ${colors.borderActive}`,
    borderRadius: radius.lg,
    padding: '18px 24px',
    boxShadow: shadow.glow,
  } as CSSProperties,

  // 浏览器窗口框架
  browserFrame: {
    background: colors.bgCard,
    borderRadius: radius.lg,
    boxShadow: shadow.lg,
    overflow: 'hidden',
    border: `1px solid ${colors.border}`,
  } as CSSProperties,

  // 浏览器顶栏
  browserTopBar: {
    background: colors.bgMediumGray,
    padding: '12px 16px',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    borderBottom: `1px solid ${colors.border}`,
  } as CSSProperties,
};

// ============================================
// 🔧 工具函数
// ============================================

/**
 * 生成背景光晕
 */
export const createGlow = (
  color: 'primary' | 'accent' | 'success' = 'primary',
  opacity: number = 0.15,
  size: number = 600
): CSSProperties => {
  const colorMap = {
    primary: '59, 145, 255',
    accent: '192, 105, 255',
    success: '82, 196, 26',
  };

  return {
    position: 'absolute',
    width: size,
    height: size,
    borderRadius: '50%',
    background: `radial-gradient(circle, rgba(${colorMap[color]}, ${opacity}) 0%, transparent 60%)`,
    pointerEvents: 'none',
  };
};

/**
 * 生成网格背景
 */
export const createGrid = (
  color: string = 'rgba(59, 145, 255, 0.03)',
  size: number = 60
): CSSProperties => ({
  position: 'absolute',
  inset: 0,
  backgroundImage: `
    linear-gradient(${color} 1px, transparent 1px),
    linear-gradient(90deg, ${color} 1px, transparent 1px)
  `,
  backgroundSize: `${size}px ${size}px`,
  pointerEvents: 'none',
});

// ============================================
// 📋 使用示例
// ============================================
/*
import {
  colors,
  font,
  style,
  springConfig,
  components,
  createGlow,
  createGrid,
} from './design-system';
import { spring, interpolate } from 'remotion';

// 渐变标题
<h1 style={{ ...font.h1, ...style.gradientText }}>
  AI Site Builder
</h1>

// AI 头像
<div style={components.aiAvatar(48)}>
  <span style={{ color: '#fff', fontSize: 18, fontWeight: 600 }}>AI</span>
</div>

// AI 消息气泡
<div style={components.aiBubble}>
  <p style={{ ...font.body, color: colors.textPrimary, margin: 0 }}>
    消息内容
  </p>
</div>

// 选项卡片
<div style={isActive ? components.optionCardActive : components.optionCard}>
  选项内容
</div>

// CTA 按钮
<div style={components.ctaButton}>
  <span style={{ ...font.body, color: colors.textLight }}>立即体验</span>
</div>

// 弹性入场动画
const progress = spring({ frame, fps, config: springConfig.bouncy });
const opacity = interpolate(progress, [0, 1], [0, 1]);
const translateY = interpolate(progress, [0, 1], [30, 0]);

<div style={{ opacity, transform: `translateY(${translateY}px)` }}>
  动画元素
</div>

// 背景光晕
<div style={{
  ...createGlow('primary', 0.15, 600),
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
}} />

// 网格背景
<div style={createGrid()} />
*/
