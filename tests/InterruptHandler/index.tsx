/**
 * HITL 中断处理主组件
 *
 * @description 根据中断数据类型自动选择合适的渲染方式
 * @author CE Platform Team
 */

import React, { useCallback, useMemo, useState } from 'react';
import { Alert, Button } from 'antd';
import { WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { message as antdMessage } from 'antd';

import { isSimpleInterruptRequest, isHITLRequest, type HITLRequest, type SimpleInterruptRequest } from './types';
import SimpleInterruptOptions from './SimpleInterruptOptions';
import HITLInput from './HITLInput';
import useInterruptedActions from './useInterruptedActions';
import { isRecord } from '@/components/AICopilot/utils/common';
import { useI18n } from '@/packages/i18n';

import styles from './index.module.scss';

export interface InterruptHandlerProps {
  /** 中断数据（可以是简单选项或 HITL 请求） */
  interrupt: unknown;
  /** Stream 对象，用于提交决策 */
  stream: {
    submit: (data: Record<string, unknown>, options?: Record<string, unknown>) => void;
  };
  /** 成功回调 */
  onSuccess?: () => void;
}

/**
 * @description 获取操作标题
 * @author CE Platform Team
 */
function getActionTitle(actionRequest: { name?: string } | undefined, unknownText: string): string {
  return actionRequest?.name ?? unknownText;
}

/**
 * @description HITL 中断处理主组件
 * @author CE Platform Team
 * @example
 * ```tsx
 *  <InterruptHandler
 *    interrupt={interruptData}
 *    stream={stream}
 *    onSuccess={() => console.log('Success!')}
 *  />
 * ```
 */
const InterruptHandler: React.FC<InterruptHandlerProps> = ({ interrupt, stream, onSuccess }) => {
  const { t } = useI18n();
  const [selectedValue, setSelectedValue] = useState<string | number | boolean | undefined>();
  const [submitting, setSubmitting] = useState(false);

  // 处理简单选项的提交
  const handleSimpleSelect = useCallback(
    async (value: string | number | boolean) => {
      setSelectedValue(value);
      setSubmitting(true);

      try {
        stream.submit(
          {},
          {
            command: {
              resume: value
            }
          }
        );
        antdMessage.success(t('aiCopilot.interrupt.decisionSubmitted'));
        onSuccess?.();
      } catch {
        // Error submitting decision
        antdMessage.error(t('aiCopilot.interrupt.decisionSubmitFailed'));
      } finally {
        setSubmitting(false);
        setSelectedValue(undefined);
      }
    },
    [stream, onSuccess, t]
  );

  // 检测中断类型
  const interruptType = useMemo(() => {
    if (isSimpleInterruptRequest(interrupt)) {
      return 'simple';
    }

    // 检查是否为 Interrupt 对象包装的数据
    if (isRecord(interrupt)) {
      const value = interrupt.value;
      if (isSimpleInterruptRequest({ id: interrupt.id, value })) {
        return 'simple';
      }
      if (isHITLRequest(value)) {
        return 'hitl';
      }
    }

    if (isHITLRequest(interrupt)) {
      return 'hitl';
    }

    return 'unknown';
  }, [interrupt]);

  // 提取实际数据
  const interruptData = useMemo(() => {
    if (interruptType === 'simple') {
      if (isSimpleInterruptRequest(interrupt)) {
        return interrupt;
      }
      if (isRecord(interrupt)) {
        return { id: interrupt.id as string, value: interrupt.value } as SimpleInterruptRequest;
      }
    }

    if (interruptType === 'hitl') {
      if (isHITLRequest(interrupt)) {
        return { value: interrupt };
      }
      if (isRecord(interrupt) && isHITLRequest(interrupt.value)) {
        return interrupt as { value: HITLRequest };
      }
    }

    return null;
  }, [interrupt, interruptType]);

  // HITL Hook
  const hitlActions = useInterruptedActions({
    interrupt: interruptData as { value?: HITLRequest },
    stream
  });

  // 简单选项渲染
  if (interruptType === 'simple' && interruptData) {
    return (
      <div className={styles.root}>
        <SimpleInterruptOptions
          interrupt={interruptData as SimpleInterruptRequest}
          onSelect={handleSimpleSelect}
          loading={submitting}
          selectedValue={selectedValue}
        />
      </div>
    );
  }

  // HITL 渲染
  if (interruptType === 'hitl' && interruptData) {
    const hitlValue = (interruptData as { value: HITLRequest }).value;
    const actionRequest = hitlValue.action_requests?.[0];
    const actionTitle = getActionTitle(actionRequest, t('aiCopilot.interrupt.unknownOperation'));

    return (
      <div className={styles.root}>
        <div className={styles.hitlContainer}>
          {/* Header */}
          <div className={styles.header}>
            <div className={styles.headerIcon}>
              <WarningOutlined />
            </div>
            <div className={styles.headerContent}>
              <h3 className={styles.headerTitle}>{actionTitle}</h3>
              <p className={styles.headerDesc}>{t('aiCopilot.interrupt.needConfirmation')}</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className={styles.actionButtons}>
            <Button
              icon={<CheckCircleOutlined />}
              onClick={hitlActions.handleResolve}
              disabled={hitlActions.loading}
            >
              {t('aiCopilot.interrupt.markAsResolved')}
            </Button>
          </div>

          {/* Input Area */}
          <HITLInput
            interruptValue={hitlValue}
            humanResponse={hitlActions.humanResponse}
            supportsMultipleMethods={hitlActions.supportsMultipleMethods}
            approveAllowed={hitlActions.approveAllowed}
            hasEdited={hitlActions.hasEdited}
            hasAddedResponse={hitlActions.hasAddedResponse}
            initialValues={hitlActions.initialHumanInterruptEditValue.current}
            isLoading={hitlActions.loading}
            selectedSubmitType={hitlActions.selectedSubmitType}
            setHumanResponse={hitlActions.setHumanResponse}
            setSelectedSubmitType={hitlActions.setSelectedSubmitType}
            setHasAddedResponse={hitlActions.setHasAddedResponse}
            setHasEdited={hitlActions.setHasEdited}
            handleSubmit={hitlActions.handleSubmit}
          />

          {/* Success Message */}
          {hitlActions.streamFinished && (
            <Alert
              type='success'
              icon={<CheckCircleOutlined />}
              message={t('aiCopilot.interrupt.hitl.graphCallCompleted')}
              className={styles.successAlert}
            />
          )}
        </div>
      </div>
    );
  }

  // 未知类型，显示原始 JSON
  return (
    <div className={styles.root}>
      <Alert
        type='warning'
        showIcon
        message='中断请求'
        description={
          <pre className={styles.jsonPre}>{JSON.stringify(interrupt, null, 2)}</pre>
        }
      />
    </div>
  );
};

export default InterruptHandler;
