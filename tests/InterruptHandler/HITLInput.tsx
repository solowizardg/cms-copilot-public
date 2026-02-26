/**
 * HITL 输入组件
 *
 * @description 处理批准、编辑、拒绝等操作的输入界面
 * @author CE Platform Team
 */

import React, { useRef } from 'react';
import { Button, Input, Divider } from 'antd';
import {
  CheckOutlined,
  CloseOutlined,
  EditOutlined,
  UndoOutlined,
  FileTextOutlined
} from '@ant-design/icons';

import type { DecisionWithEdits, HITLRequest, SubmitType } from './types';
import { prettifyText, haveArgsChanged } from './utils';
import MarkdownRender from '@/components/AICopilot/components/MarkdownRender';
import { useI18n } from '@/packages/i18n';

import styles from './HITLInput.module.scss';

const { TextArea } = Input;

interface ArgsRendererProps {
  args: Record<string, unknown>;
}

/**
 * @description 渲染参数列表
 * @author CE Platform Team
 */
const ArgsRenderer: React.FC<ArgsRendererProps> = ({ args }) => {
  return (
    <div className={styles.argsContainer}>
      {Object.entries(args).map(([key, value]) => {
        const stringValue =
          typeof value === 'string' || typeof value === 'number'
            ? value.toString()
            : JSON.stringify(value, null);

        return (
          <div key={`args-${key}`} className={styles.argItem}>
            <div className={styles.argLabel}>
              <FileTextOutlined className={styles.argIcon} />
              <span>{prettifyText(key)}</span>
            </div>
            <div className={styles.argValue}>
              <MarkdownRender content={stringValue} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

interface ApproveOnlyProps {
  isLoading: boolean;
  actionRequestArgs: Record<string, unknown>;
  handleSubmit: (e: React.MouseEvent<HTMLElement>) => void;
  approveText: string;
}

/**
 * @description 仅批准操作卡片
 * @author CE Platform Team
 */
const ApproveOnly: React.FC<ApproveOnlyProps> = ({ isLoading, actionRequestArgs, handleSubmit, approveText }) => {
  return (
    <div className={styles.card}>
      {Object.keys(actionRequestArgs).length > 0 && <ArgsRenderer args={actionRequestArgs} />}
      <Button
        type='primary'
        block
        size='large'
        disabled={isLoading}
        onClick={handleSubmit}
        icon={<CheckOutlined />}
        className={styles.submitButton}
      >
        {approveText}
      </Button>
    </div>
  );
};

interface EditActionCardProps {
  humanResponse: DecisionWithEdits[];
  isLoading: boolean;
  initialValues: Record<string, string>;
  actionArgs: Record<string, unknown>;
  onEditChange: (text: string | string[], response: DecisionWithEdits, key: string | string[]) => void;
  handleSubmit: (e: React.MouseEvent<HTMLElement> | React.KeyboardEvent) => void;
  i18nTexts: {
    editApprove: string;
    editParams: string;
    approveExecute: string;
    submitChanges: string;
    reset: string;
    ctrlEnterHint: string;
  };
}

/**
 * @description 编辑操作卡片
 * @author CE Platform Team
 */
const EditActionCard: React.FC<EditActionCardProps> = ({
  humanResponse,
  isLoading,
  initialValues,
  actionArgs,
  onEditChange,
  handleSubmit,
  i18nTexts
}) => {
  const defaultRows = useRef<Record<string, number>>({});
  const editResponse = humanResponse.find(response => response.type === 'edit');
  const approveResponse = humanResponse.find(response => response.type === 'approve');

  if (
    !editResponse ||
    editResponse.type !== 'edit' ||
    typeof editResponse.edited_action !== 'object' ||
    !editResponse.edited_action
  ) {
    if (approveResponse) {
      return <ApproveOnly actionRequestArgs={actionArgs} isLoading={isLoading} handleSubmit={handleSubmit} approveText={i18nTexts.approveExecute} />;
    }
    return null;
  }

  const header = editResponse.acceptAllowed ? i18nTexts.editApprove : i18nTexts.editParams;
  const buttonText = editResponse.acceptAllowed && !editResponse.editsMade ? i18nTexts.approveExecute : i18nTexts.submitChanges;

  const handleReset = () => {
    if (!editResponse.edited_action?.args) {
      return;
    }

    const keysToReset: string[] = [];
    const valuesToReset: string[] = [];
    Object.entries(initialValues).forEach(([key, value]) => {
      if (key in editResponse.edited_action.args) {
        const stringValue =
          typeof value === 'string' || typeof value === 'number' ? value.toString() : JSON.stringify(value, null);
        keysToReset.push(key);
        valuesToReset.push(stringValue);
      }
    });

    if (keysToReset.length > 0 && valuesToReset.length > 0) {
      onEditChange(valuesToReset, editResponse, keysToReset);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.cardHeaderTitle}>
          <EditOutlined className={styles.cardHeaderIcon} />
          <span>{header}</span>
        </div>
        <Button type='text' size='small' icon={<UndoOutlined />} onClick={handleReset} className={styles.resetButton}>
          {i18nTexts.reset}
        </Button>
      </div>

      <div className={styles.editFields}>
        {Object.entries(editResponse.edited_action.args).map(([key, value], idx) => {
          const stringValue =
            typeof value === 'string' || typeof value === 'number' ? value.toString() : JSON.stringify(value, null);

          if (defaultRows.current[key] === undefined) {
            defaultRows.current[key] = !stringValue.length ? 3 : Math.max(Math.ceil(stringValue.length / 30), 4);
          }

          return (
            <div className={styles.editField} key={`allow-edit-args--${key}-${idx}`}>
              <label className={styles.editFieldLabel}>
                <FileTextOutlined className={styles.editFieldIcon} />
                {prettifyText(key)}
              </label>
              <TextArea
                disabled={isLoading}
                className={styles.editFieldInput}
                value={stringValue}
                onChange={event => onEditChange(event.target.value, editResponse, key)}
                onKeyDown={handleKeyDown}
                rows={defaultRows.current[key] || 4}
                placeholder={`输入 ${prettifyText(key)}...`}
              />
            </div>
          );
        })}
      </div>

      <div className={styles.cardFooter}>
        <span className={styles.cardFooterHint}>{i18nTexts.ctrlEnterHint}</span>
        <Button type='primary' disabled={isLoading} onClick={handleSubmit} icon={<CheckOutlined />}>
          {buttonText}
        </Button>
      </div>
    </div>
  );
};

interface RejectActionCardProps {
  humanResponse: DecisionWithEdits[];
  isLoading: boolean;
  onChange: (value: string, response: DecisionWithEdits) => void;
  handleSubmit: (e: React.MouseEvent<HTMLElement> | React.KeyboardEvent) => void;
  showArgs: boolean;
  actionArgs: Record<string, unknown>;
  i18nTexts: {
    rejectOperation: string;
    rejectReason: string;
    rejectReasonPlaceholder: string;
    confirmReject: string;
    reset: string;
    ctrlEnterHint: string;
  };
}

/**
 * @description 拒绝操作卡片
 * @author CE Platform Team
 */
const RejectActionCard: React.FC<RejectActionCardProps> = ({
  humanResponse,
  isLoading,
  onChange,
  handleSubmit,
  showArgs,
  actionArgs,
  i18nTexts
}) => {
  const rejectResponse = humanResponse.find(response => response.type === 'reject');

  if (!rejectResponse) {
    return null;
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  return (
    <div className={`${styles.card} ${styles.rejectCard}`}>
      <div className={styles.cardHeader}>
        <div className={styles.cardHeaderTitle}>
          <CloseOutlined className={`${styles.cardHeaderIcon} ${styles.rejectIcon}`} />
          <span>{i18nTexts.rejectOperation}</span>
        </div>
        <Button
          type='text'
          size='small'
          icon={<UndoOutlined />}
          onClick={() => onChange('', rejectResponse)}
          className={styles.resetButton}
        >
          {i18nTexts.reset}
        </Button>
      </div>

      {showArgs && <ArgsRenderer args={actionArgs} />}

      <div className={styles.editField}>
        <label className={styles.editFieldLabel}>
          <FileTextOutlined className={styles.editFieldIcon} />
          {i18nTexts.rejectReason}
        </label>
        <TextArea
          disabled={isLoading}
          className={styles.editFieldInput}
          value={rejectResponse.message ?? ''}
          onChange={event => onChange(event.target.value, rejectResponse)}
          onKeyDown={handleKeyDown}
          rows={4}
          placeholder={i18nTexts.rejectReasonPlaceholder}
        />
      </div>

      <div className={styles.cardFooter}>
        <span className={styles.cardFooterHint}>{i18nTexts.ctrlEnterHint}</span>
        <Button danger disabled={isLoading} onClick={handleSubmit} icon={<CloseOutlined />}>
          {i18nTexts.confirmReject}
        </Button>
      </div>
    </div>
  );
};

export interface HITLInputProps {
  /** HITL 请求数据 */
  interruptValue: HITLRequest;
  /** 人工响应列表 */
  humanResponse: DecisionWithEdits[];
  /** 是否支持多种方法 */
  supportsMultipleMethods: boolean;
  /** 是否允许批准 */
  approveAllowed: boolean;
  /** 是否已编辑 */
  hasEdited: boolean;
  /** 是否已添加响应 */
  hasAddedResponse: boolean;
  /** 初始值 */
  initialValues: Record<string, string>;
  /** 是否加载中 */
  isLoading: boolean;
  /** 选中的提交类型 */
  selectedSubmitType: SubmitType | undefined;

  /** 设置人工响应 */
  setHumanResponse: React.Dispatch<React.SetStateAction<DecisionWithEdits[]>>;
  /** 设置选中的提交类型 */
  setSelectedSubmitType: React.Dispatch<React.SetStateAction<SubmitType | undefined>>;
  /** 设置是否已添加响应 */
  setHasAddedResponse: React.Dispatch<React.SetStateAction<boolean>>;
  /** 设置是否已编辑 */
  setHasEdited: React.Dispatch<React.SetStateAction<boolean>>;
  /** 提交处理函数 */
  handleSubmit: (e: React.MouseEvent<HTMLElement> | React.KeyboardEvent) => Promise<void> | void;
}

/**
 * @description HITL 输入组件
 * @author CE Platform Team
 * @example
 * ```tsx
 *  <HITLInput
 *    interruptValue={hitlRequest}
 *    humanResponse={humanResponse}
 *    supportsMultipleMethods={supportsMultipleMethods}
 *    approveAllowed={approveAllowed}
 *    hasEdited={hasEdited}
 *    hasAddedResponse={hasAddedResponse}
 *    initialValues={initialValues}
 *    isLoading={loading}
 *    selectedSubmitType={selectedSubmitType}
 *    setHumanResponse={setHumanResponse}
 *    setSelectedSubmitType={setSelectedSubmitType}
 *    setHasAddedResponse={setHasAddedResponse}
 *    setHasEdited={setHasEdited}
 *    handleSubmit={handleSubmit}
 *  />
 * ```
 */
const HITLInput: React.FC<HITLInputProps> = ({
  interruptValue,
  humanResponse,
  approveAllowed,
  hasEdited,
  hasAddedResponse,
  initialValues,
  isLoading,
  supportsMultipleMethods,
  selectedSubmitType,
  setHumanResponse,
  setSelectedSubmitType,
  setHasAddedResponse,
  setHasEdited,
  handleSubmit
}) => {
  const { t } = useI18n();
  const allowedDecisions = interruptValue.review_configs?.[0]?.allowed_decisions ?? [];
  const actionRequest = interruptValue.action_requests?.[0];
  const actionArgs = actionRequest?.args ?? {};
  const isEditAllowed = allowedDecisions.includes('edit');
  const isRejectAllowed = allowedDecisions.includes('reject');
  const hasArgs = Object.keys(actionArgs).length > 0;
  const showArgsInReject = hasArgs && !isEditAllowed && !approveAllowed && isRejectAllowed;
  const showArgsOutsideCards = hasArgs && !showArgsInReject && !isEditAllowed && !approveAllowed;

  const onEditChange = (change: string | string[], response: DecisionWithEdits, key: string | string[]) => {
    if ((Array.isArray(change) && !Array.isArray(key)) || (!Array.isArray(change) && Array.isArray(key))) {
      // Unable to update edited values - type mismatch
      return;
    }

    let valuesChanged = true;
    if (response.type === 'edit' && response.edited_action) {
      const updatedArgs = { ...(response.edited_action.args || {}) };

      if (Array.isArray(change) && Array.isArray(key)) {
        change.forEach((value, index) => {
          if (index < key.length) {
            updatedArgs[key[index]] = value;
          }
        });
      } else {
        updatedArgs[key as string] = change as string;
      }

      valuesChanged = haveArgsChanged(updatedArgs, initialValues);
    }

    if (!valuesChanged) {
      setHasEdited(false);
      if (approveAllowed) {
        setSelectedSubmitType('approve');
      } else if (hasAddedResponse) {
        setSelectedSubmitType('reject');
      }
    } else {
      setSelectedSubmitType('edit');
      setHasEdited(true);
    }

    setHumanResponse(prev => {
      if (response.type !== 'edit' || !response.edited_action) {
        // Mismatched response type for edit
        return prev;
      }

      const newArgs =
        Array.isArray(change) && Array.isArray(key)
          ? {
              ...response.edited_action.args,
              ...Object.fromEntries(key.map((k, index) => [k, change[index]]))
            }
          : {
              ...response.edited_action.args,
              [key as string]: change as string
            };

      const newEdit: DecisionWithEdits = {
        type: 'edit',
        edited_action: {
          name: response.edited_action.name,
          args: newArgs
        }
      };

      return prev.map(existing => {
        if (existing.type !== 'edit') {
          return existing;
        }

        if (existing.acceptAllowed) {
          return {
            ...newEdit,
            acceptAllowed: true,
            editsMade: valuesChanged
          };
        }

        return newEdit;
      });
    });
  };

  const onRejectChange = (change: string, response: DecisionWithEdits) => {
    if (response.type !== 'reject') {
      // Mismatched response type for rejection
      return;
    }

    const trimmed = change.trim();
    setHasAddedResponse(!!trimmed);

    if (!trimmed) {
      if (hasEdited) {
        setSelectedSubmitType('edit');
      } else if (approveAllowed) {
        setSelectedSubmitType('approve');
      }
    } else {
      setSelectedSubmitType('reject');
    }

    setHumanResponse(prev =>
      prev.map(existing => (existing.type === 'reject' ? { type: 'reject', message: change } : existing))
    );
  };

  // i18n texts for sub-components
  const editI18nTexts = {
    editApprove: t('aiCopilot.interrupt.hitl.editApprove'),
    editParams: t('aiCopilot.interrupt.hitl.editParams'),
    approveExecute: t('aiCopilot.interrupt.hitl.approveExecute'),
    submitChanges: t('aiCopilot.interrupt.hitl.submitChanges'),
    reset: t('aiCopilot.interrupt.hitl.reset'),
    ctrlEnterHint: t('aiCopilot.interrupt.hitl.ctrlEnterHint')
  };

  const rejectI18nTexts = {
    rejectOperation: t('aiCopilot.interrupt.hitl.rejectOperation'),
    rejectReason: t('aiCopilot.interrupt.hitl.rejectReason'),
    rejectReasonPlaceholder: t('aiCopilot.interrupt.hitl.rejectReasonPlaceholder'),
    confirmReject: t('aiCopilot.interrupt.hitl.confirmReject'),
    reset: t('aiCopilot.interrupt.hitl.reset'),
    ctrlEnterHint: t('aiCopilot.interrupt.hitl.ctrlEnterHint')
  };

  return (
    <div className={styles.root}>
      {showArgsOutsideCards && (
        <div className={styles.argsCard}>
          <ArgsRenderer args={actionArgs} />
        </div>
      )}

      <div className={styles.cardsContainer}>
        <EditActionCard
          humanResponse={humanResponse}
          isLoading={isLoading}
          initialValues={initialValues}
          actionArgs={actionArgs}
          onEditChange={onEditChange}
          handleSubmit={handleSubmit}
          i18nTexts={editI18nTexts}
        />

        {supportsMultipleMethods && (
          <div className={styles.dividerContainer}>
            <Divider className={styles.divider}>{t('aiCopilot.interrupt.hitl.or')}</Divider>
          </div>
        )}

        <RejectActionCard
          humanResponse={humanResponse}
          isLoading={isLoading}
          showArgs={showArgsInReject}
          actionArgs={actionArgs}
          onChange={onRejectChange}
          handleSubmit={handleSubmit}
          i18nTexts={rejectI18nTexts}
        />

        {isLoading && (
          <div className={styles.loadingHint}>
            <span className={styles.loadingSpinner} />
            <span>{t('aiCopilot.interrupt.hitl.submittingDecision')}</span>
          </div>
        )}

        {selectedSubmitType && supportsMultipleMethods && (
          <div className={styles.selectionHint}>
            {t('aiCopilot.interrupt.hitl.currentSelection')}: <span className={styles.selectionType}>{prettifyText(selectedSubmitType)}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default HITLInput;
