/**
 * HITL (Human-in-the-Loop) 中断处理类型定义
 *
 * @description 定义中断请求、决策类型和相关数据结构
 * @author CE Platform Team
 */

/** 决策类型：批准、编辑、拒绝 */
export type DecisionType = 'approve' | 'edit' | 'reject';

/** 操作定义 */
export interface Action {
  name: string;
  args: Record<string, unknown>;
}

/** 操作请求 */
export interface ActionRequest {
  name: string;
  args: Record<string, unknown>;
  description?: string;
}

/** 审核配置 */
export interface ReviewConfig {
  action_name: string;
  allowed_decisions: DecisionType[];
  args_schema?: Record<string, unknown>;
}

/** HITL 请求数据结构 */
export interface HITLRequest {
  action_requests: ActionRequest[];
  review_configs: ReviewConfig[];
}

/** 基础决策类型 */
export type Decision =
  | { type: 'approve' }
  | { type: 'reject'; message?: string }
  | { type: 'edit'; edited_action: Action };

/** 带编辑状态的决策类型 */
export type DecisionWithEdits =
  | { type: 'approve' }
  | { type: 'reject'; message?: string }
  | {
      type: 'edit';
      edited_action: Action;
      acceptAllowed?: boolean;
      editsMade?: boolean;
    };

/** 提交类型 */
export type SubmitType = DecisionType;

/**
 * 简化的中断选项（用于简单的选项按钮场景）
 * 如："批准并执行"、"跳过此步"、"取消全部"
 */
export interface SimpleInterruptOption {
  label: string;
  /** 支持 string | number | boolean，以便后端可以返回布尔型选项 */
  value: string | number | boolean;
}

/**
 * 简化的中断请求（用于简单的问答选项场景）
 */
export interface SimpleInterruptRequest {
  id: string;
  value: {
    question: string;
    options: SimpleInterruptOption[];
  };
}

/**
 * 检查是否为简单的中断请求格式
 */
export function isSimpleInterruptRequest(data: unknown): data is SimpleInterruptRequest {
  if (!data || typeof data !== 'object') return false;
  const obj = data as Record<string, unknown>;
  if (!obj.id || typeof obj.id !== 'string') return false;
  if (!obj.value || typeof obj.value !== 'object') return false;
  const value = obj.value as Record<string, unknown>;
  if (typeof value.question !== 'string') return false;
  if (!Array.isArray(value.options)) return false;
  return value.options.every(
    (opt: unknown) =>
      typeof opt === 'object' &&
      opt !== null &&
      typeof (opt as Record<string, unknown>).label === 'string' &&
      (typeof (opt as Record<string, unknown>).value === 'string' ||
        typeof (opt as Record<string, unknown>).value === 'boolean' ||
        typeof (opt as Record<string, unknown>).value === 'number')
  );
}

/**
 * 检查是否为 HITL 请求格式
 */
export function isHITLRequest(data: unknown): data is HITLRequest {
  if (!data || typeof data !== 'object') return false;
  const obj = data as Record<string, unknown>;
  return (
    Array.isArray(obj.action_requests) &&
    obj.action_requests.length > 0 &&
    Array.isArray(obj.review_configs) &&
    obj.review_configs.length > 0
  );
}
