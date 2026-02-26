/**
 * HITL 中断操作 Hook
 *
 * @description 处理 HITL 中断请求的提交逻辑
 * @author CE Platform Team
 */

import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction, type MutableRefObject } from 'react';
import { message as antdMessage } from 'antd';

import type { Decision, DecisionWithEdits, HITLRequest, SubmitType } from './types';
import { buildDecisionFromState, createDefaultHumanResponse } from './utils';
import { useI18n } from '@/packages/i18n';

interface UseInterruptedActionsInput {
  /** 中断请求数据，可为 null 或 undefined */
  interrupt?: { value?: HITLRequest } | null;
  /** Stream 对象，用于提交决策 */
  stream: {
    submit: (data: Record<string, unknown>, options?: Record<string, unknown>) => void;
  };
} 

interface UseInterruptedActionsValue {
  /** 提交处理函数 */
  handleSubmit: (e?: React.MouseEvent | React.KeyboardEvent) => Promise<void>;
  /** 标记为已解决 */
  handleResolve: (e?: React.MouseEvent) => Promise<void>;
  /** 是否正在流式传输 */
  streaming: boolean;
  /** 流是否完成 */
  streamFinished: boolean;
  /** 是否加载中 */
  loading: boolean;
  /** 是否支持多种方法 */
  supportsMultipleMethods: boolean;
  /** 是否已编辑 */
  hasEdited: boolean;
  /** 是否已添加响应 */
  hasAddedResponse: boolean;
  /** 是否允许批准 */
  approveAllowed: boolean;
  /** 人工响应列表 */
  humanResponse: DecisionWithEdits[];
  /** 选中的提交类型 */
  selectedSubmitType: SubmitType | undefined;
  /** 设置选中的提交类型 */
  setSelectedSubmitType: Dispatch<SetStateAction<SubmitType | undefined>>;
  /** 设置人工响应 */
  setHumanResponse: Dispatch<SetStateAction<DecisionWithEdits[]>>;
  /** 设置是否已添加响应 */
  setHasAddedResponse: Dispatch<SetStateAction<boolean>>;
  /** 设置是否已编辑 */
  setHasEdited: Dispatch<SetStateAction<boolean>>;
  /** 初始编辑值的 ref */
  initialHumanInterruptEditValue: MutableRefObject<Record<string, string>>;
}

/**
 * @description HITL 中断操作 Hook
 * @author CE Platform Team
 * @param interrupt  中断请求数据
 * @param stream  Stream 对象
 * @example
 * ```tsx
 *  const {
 *    handleSubmit,
 *    loading,
 *    humanResponse,
 *    selectedSubmitType,
 *    setSelectedSubmitType
 *  } = useInterruptedActions({ interrupt, stream });
 * ```
 * @returns {UseInterruptedActionsValue} Hook 返回值
 */
export default function useInterruptedActions({
  interrupt,
  stream
}: UseInterruptedActionsInput): UseInterruptedActionsValue {
  const { t } = useI18n();
  const [humanResponse, setHumanResponse] = useState<DecisionWithEdits[]>([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamFinished, setStreamFinished] = useState(false);
  const [selectedSubmitType, setSelectedSubmitType] = useState<SubmitType>();
  const [hasEdited, setHasEdited] = useState(false);
  const [hasAddedResponse, setHasAddedResponse] = useState(false);
  const [approveAllowed, setApproveAllowed] = useState(false);
  const initialHumanInterruptEditValue = useRef<Record<string, string>>({});

  useEffect(() => {
    const hitlValue = interrupt?.value as HITLRequest | undefined;
    initialHumanInterruptEditValue.current = {};

    if (!hitlValue) {
      setHumanResponse([]);
      setSelectedSubmitType(undefined);
      setApproveAllowed(false);
      setHasEdited(false);
      setHasAddedResponse(false);
      return;
    }

    try {
      const { responses, defaultSubmitType, hasApprove } = createDefaultHumanResponse(
        hitlValue,
        initialHumanInterruptEditValue
      );
      setHumanResponse(responses);
      setSelectedSubmitType(defaultSubmitType);
      setApproveAllowed(hasApprove);
      setHasEdited(false);
      setHasAddedResponse(false);
    } catch {
      // Error formatting human response state, reset to defaults
      setHumanResponse([]);
      setSelectedSubmitType(undefined);
      setApproveAllowed(false);
    }
  }, [interrupt]);

  const resumeRun = useCallback(
    (decisions: Decision[]): boolean => {
      try {
        stream.submit(
          {},
          {
            command: {
              resume: {
                decisions
              }
            }
          }
        );
        return true;
      } catch {
        // Error sending human response
        return false;
      }
    },
    [stream]
  );

  const handleSubmit = useCallback(
    async (e?: React.MouseEvent | React.KeyboardEvent) => {
      e?.preventDefault();
      const { decision, errorKey } = buildDecisionFromState(humanResponse, selectedSubmitType);

      if (!decision) {
        const errorMessage = errorKey
          ? t(`aiCopilot.interrupt.hitl.${errorKey}`)
          : t('aiCopilot.interrupt.hitl.unsupportedResponseType');
        antdMessage.error(errorMessage);
        return;
      }

      if (errorKey) {
        antdMessage.error(t(`aiCopilot.interrupt.hitl.${errorKey}`));
        return;
      }

      let errorOccurred = false;
      initialHumanInterruptEditValue.current = {};

      try {
        setLoading(true);
        setStreaming(true);

        const resumedSuccessfully = resumeRun([decision]);
        if (!resumedSuccessfully) {
          errorOccurred = true;
          return;
        }

        antdMessage.success(t('aiCopilot.interrupt.responseSubmitted'));
        setStreamFinished(true);
      } catch {
        // Error sending human response
        errorOccurred = true;
        antdMessage.error(t('aiCopilot.interrupt.responseSubmitFailed'));
      } finally {
        setStreaming(false);
        setLoading(false);
        if (errorOccurred) {
          setStreamFinished(false);
        }
      }
    },
    [humanResponse, selectedSubmitType, resumeRun, t]
  );

  const handleResolve = useCallback(
    async (e?: React.MouseEvent) => {
      e?.preventDefault();
      setLoading(true);
      initialHumanInterruptEditValue.current = {};

      try {
        stream.submit(
          {},
          {
            command: {
              goto: '__end__'
            }
          }
        );

        antdMessage.success(t('aiCopilot.interrupt.markedAsResolved'));
      } catch {
        // Error marking thread as resolved
        antdMessage.error(t('aiCopilot.interrupt.markAsResolvedFailed'));
      } finally {
        setLoading(false);
      }
    },
    [stream, t]
  );

  const supportsMultipleMethods =
    humanResponse.filter(response => ['edit', 'approve', 'reject'].includes(response.type)).length > 1;

  return {
    handleSubmit,
    handleResolve,
    humanResponse,
    selectedSubmitType,
    streaming,
    streamFinished,
    loading,
    supportsMultipleMethods,
    hasEdited,
    hasAddedResponse,
    approveAllowed,
    setSelectedSubmitType,
    setHumanResponse,
    setHasAddedResponse,
    setHasEdited,
    initialHumanInterruptEditValue
  };
}
