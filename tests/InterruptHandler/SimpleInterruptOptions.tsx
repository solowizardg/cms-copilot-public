/**
 * 简单中断选项组件
 *
 * @description 用于渲染简单的中断选项按钮（如"批准并执行"、"跳过此步"、"取消全部"）
 * @author CE Platform Team
 */

import React from 'react';
import { Button } from 'antd';
import { CheckOutlined, StopOutlined, CloseOutlined, QuestionCircleOutlined } from '@ant-design/icons';

import type { SimpleInterruptRequest } from './types';
import { useI18n } from '@/packages/i18n';

import styles from './SimpleInterruptOptions.module.scss';

export interface SimpleInterruptOptionsProps {
  /** 中断请求数据 */
  interrupt: SimpleInterruptRequest;
  /** 点击选项回调 */
  onSelect: (value: string | number | boolean) => void;
  /** 是否加载中 */
  loading?: boolean;
  /** 当前选中的值（用于显示加载状态） */
  selectedValue?: string | number | boolean;
}

/**
 * @description 根据选项值获取对应的图标
 * @author CE Platform Team
 * @param value  选项值
 * @returns {React.ReactNode} 图标组件
 */
const getOptionIcon = (value: string | number | boolean): React.ReactNode => {
  const v = String(value);
  switch (v) {
    case 'approve':
      return <CheckOutlined />;
    case 'skip':
      return <StopOutlined />;
    case 'cancel':
      return <CloseOutlined />;
    default:
      return <QuestionCircleOutlined />;
  }
};

/**
 * @description 根据选项值获取按钮类型
 * @author CE Platform Team
 * @param value  选项值
 * @returns {'primary' | 'default' | 'dashed'} 按钮类型
 */
const getButtonType = (value: string | number | boolean): 'primary' | 'default' | 'dashed' => {
  const v = String(value);
  switch (v) {
    case 'approve':
      return 'primary';
    case 'skip':
      return 'default';
    case 'cancel':
      return 'dashed';
    default:
      return 'default';
  }
};

/**
 * @description 根据选项值获取按钮是否危险
 * @author CE Platform Team
 * @param value  选项值
 * @returns {boolean} 是否为危险按钮
 */
const isDangerButton = (value: string | number | boolean): boolean => {
  return String(value) === 'cancel';
};

/**
 * @description 简单中断选项组件
 * @author CE Platform Team
 * @example
 * ```tsx
 *  <SimpleInterruptOptions
 *    interrupt={interruptData}
 *    onSelect={(value) => handleDecision(value)}
 *    loading={isSubmitting}
 *  />
 * ```
 */
const SimpleInterruptOptions: React.FC<SimpleInterruptOptionsProps> = ({
  interrupt,
  onSelect,
  loading = false,
  selectedValue
}) => {
  const { t } = useI18n();
  const { question, options } = interrupt.value;

  // Map option values to i18n keys
  const getOptionLabel = (value: string | number | boolean, fallbackLabel: string): string => {
    const i18nMap: Record<string, string> = {
      approve: t('aiCopilot.interrupt.simple.approve'),
      skip: t('aiCopilot.interrupt.simple.skip'),
      cancel: t('aiCopilot.interrupt.simple.cancel')
    };
    return i18nMap[String(value)] ?? fallbackLabel;
  };

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <QuestionCircleOutlined className={styles.headerIcon} />
        <span className={styles.headerText}>{t('aiCopilot.interrupt.needConfirmation')}</span>
      </div>

      <div className={styles.question}>{question}</div>

      <div className={styles.options}>
        {options.map((option, idx) => (
          <Button
            key={`${idx}-${String(option.value)}-${option.label}`}
            type={getButtonType(option.value)}
            danger={isDangerButton(option.value)}
            icon={getOptionIcon(option.value)}
            onClick={() => onSelect(option.value)}
            loading={loading && selectedValue === option.value}
            disabled={loading}
            className={styles.optionButton}
            style={{
              background: String(option.value) === 'approve' ? '#10B981' : undefined,
              borderColor: String(option.value) === 'approve' ? '#10B981' : undefined
            }}
          >
            {getOptionLabel(option.value, option.label)}
          </Button>
        ))}
      </div>
    </div>
  );
};

export default SimpleInterruptOptions;
