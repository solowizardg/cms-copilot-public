/**
 * HITL 中断处理工具函数
 *
 * @description 提供决策构建、参数验证等工具方法
 * @author CE Platform Team
 */

import type { MutableRefObject } from 'react';
import type {
  Action,
  Decision,
  DecisionWithEdits,
  HITLRequest,
  SubmitType
} from './types';

/**
 * @description 美化文本显示（下划线转空格，首字母大写）
 * @author CE Platform Team
 * @param text  原始文本
 * @returns {string} 美化后的文本
 */
export function prettifyText(text: string): string {
  return text
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

/**
 * @description 创建默认的人工响应状态
 * @author CE Platform Team
 * @param hitlRequest  HITL 请求数据
 * @param initialHumanInterruptEditValue  初始编辑值的 ref
 * @returns {{ responses: DecisionWithEdits[]; defaultSubmitType: SubmitType | undefined; hasApprove: boolean }}
 */
export function createDefaultHumanResponse(
  hitlRequest: HITLRequest,
  initialHumanInterruptEditValue: MutableRefObject<Record<string, string>>
): {
  responses: DecisionWithEdits[];
  defaultSubmitType: SubmitType | undefined;
  hasApprove: boolean;
} {
  const responses: DecisionWithEdits[] = [];
  const actionRequest = hitlRequest.action_requests?.[0];
  const reviewConfig =
    hitlRequest.review_configs?.find(config => config.action_name === actionRequest?.name) ??
    hitlRequest.review_configs?.[0];

  if (!actionRequest || !reviewConfig) {
    return { responses: [], defaultSubmitType: undefined, hasApprove: false };
  }

  const allowedDecisions = reviewConfig.allowed_decisions ?? [];

  if (allowedDecisions.includes('edit')) {
    Object.entries(actionRequest.args).forEach(([key, value]) => {
      const stringValue =
        typeof value === 'string' || typeof value === 'number'
          ? value.toString()
          : JSON.stringify(value, null);
      initialHumanInterruptEditValue.current = {
        ...initialHumanInterruptEditValue.current,
        [key]: stringValue
      };
    });

    const editedAction: Action = {
      name: actionRequest.name,
      args: { ...actionRequest.args }
    };

    responses.push({
      type: 'edit',
      edited_action: editedAction,
      acceptAllowed: allowedDecisions.includes('approve'),
      editsMade: false
    });
  }

  if (allowedDecisions.includes('approve')) {
    responses.push({ type: 'approve' });
  }

  if (allowedDecisions.includes('reject')) {
    responses.push({ type: 'reject', message: '' });
  }

  // 确定默认提交类型，优先级：approve > reject > edit
  let defaultSubmitType: SubmitType | undefined;

  if (allowedDecisions.includes('approve')) {
    defaultSubmitType = 'approve';
  } else if (allowedDecisions.includes('reject')) {
    defaultSubmitType = 'reject';
  } else if (allowedDecisions.includes('edit')) {
    defaultSubmitType = 'edit';
  }

  const hasApprove = allowedDecisions.includes('approve');

  return { responses, defaultSubmitType, hasApprove };
}

/**
 * @description 从状态构建决策对象
 * @author CE Platform Team
 * @param responses  响应列表
 * @param selectedSubmitType  选中的提交类型
 * @returns {{ decision?: Decision; errorKey?: string }} errorKey 用于 i18n 翻译
 */
export function buildDecisionFromState(
  responses: DecisionWithEdits[],
  selectedSubmitType: SubmitType | undefined
): { decision?: Decision; errorKey?: string } {
  if (!responses.length) {
    return { errorKey: 'enterResponse' };
  }

  const selectedDecision = responses.find(response => response.type === selectedSubmitType);

  if (!selectedDecision) {
    return { errorKey: 'noResponseSelected' };
  }

  if (selectedDecision.type === 'approve') {
    return { decision: { type: 'approve' } };
  }

  if (selectedDecision.type === 'reject') {
    const message = selectedDecision.message?.trim();
    if (!message) {
      return { errorKey: 'provideRejectReason' };
    }
    return { decision: { type: 'reject', message } };
  }

  if (selectedDecision.type === 'edit') {
    if (selectedDecision.acceptAllowed && !selectedDecision.editsMade) {
      return { decision: { type: 'approve' } };
    }

    return {
      decision: {
        type: 'edit',
        edited_action: selectedDecision.edited_action
      }
    };
  }

  return { errorKey: 'unsupportedResponseType' };
}

/**
 * @description 检查参数是否发生变化
 * @author CE Platform Team
 * @param args  当前参数
 * @param initialValues  初始值
 * @returns {boolean} 是否有变化
 */
export function haveArgsChanged(args: unknown, initialValues: Record<string, string>): boolean {
  if (typeof args !== 'object' || !args) {
    return false;
  }

  const currentValues = args as Record<string, string>;

  return Object.entries(currentValues).some(([key, value]) => {
    const valueString = ['string', 'number'].includes(typeof value)
      ? value.toString()
      : JSON.stringify(value, null);
    return initialValues[key] !== valueString;
  });
}
