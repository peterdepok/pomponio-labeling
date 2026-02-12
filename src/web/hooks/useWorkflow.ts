/**
 * Workflow state machine for streamlined auto-flow labeling.
 *
 * States: IDLE -> PRODUCT_SELECTED -> WEIGHT_CAPTURED -> LABEL_PRINTED -> IDLE
 * Weight lock, print, and completion are driven by effects in LabelingScreen.
 */

import { useCallback, useReducer } from "react";

export const WorkflowState = {
  IDLE: "idle",
  PRODUCT_SELECTED: "product_selected",
  WEIGHT_CAPTURED: "weight_captured",
  LABEL_PRINTED: "label_printed",
} as const;

export type WorkflowState = (typeof WorkflowState)[keyof typeof WorkflowState];

const TRANSITIONS: Record<WorkflowState, Set<WorkflowState>> = {
  [WorkflowState.IDLE]: new Set([WorkflowState.PRODUCT_SELECTED]),
  [WorkflowState.PRODUCT_SELECTED]: new Set([WorkflowState.WEIGHT_CAPTURED]),
  [WorkflowState.WEIGHT_CAPTURED]: new Set([WorkflowState.LABEL_PRINTED]),
  [WorkflowState.LABEL_PRINTED]: new Set([WorkflowState.IDLE]),
};

export interface WorkflowContext {
  productId: number | null;
  productName: string | null;
  sku: string | null;
  weightLb: number | null;
  barcode: string | null;
}

interface WorkflowData {
  state: WorkflowState;
  context: WorkflowContext;
}

type WorkflowAction =
  | { type: "SELECT_PRODUCT"; productId: number; name: string; sku: string }
  | { type: "CAPTURE_WEIGHT"; weightLb: number }
  | { type: "PRINT_LABEL"; barcode: string }
  | { type: "COMPLETE" }
  | { type: "CANCEL" }
  | { type: "REWEIGH" };

const EMPTY_CONTEXT: WorkflowContext = {
  productId: null,
  productName: null,
  sku: null,
  weightLb: null,
  barcode: null,
};

function workflowReducer(data: WorkflowData, action: WorkflowAction): WorkflowData {
  switch (action.type) {
    case "SELECT_PRODUCT": {
      if (!TRANSITIONS[data.state].has(WorkflowState.PRODUCT_SELECTED)) return data;
      return {
        state: WorkflowState.PRODUCT_SELECTED,
        context: {
          ...EMPTY_CONTEXT,
          productId: action.productId,
          productName: action.name,
          sku: action.sku,
        },
      };
    }
    case "CAPTURE_WEIGHT": {
      if (!TRANSITIONS[data.state].has(WorkflowState.WEIGHT_CAPTURED)) return data;
      if (action.weightLb <= 0) return data;
      return {
        state: WorkflowState.WEIGHT_CAPTURED,
        context: { ...data.context, weightLb: action.weightLb },
      };
    }
    case "PRINT_LABEL": {
      if (!TRANSITIONS[data.state].has(WorkflowState.LABEL_PRINTED)) return data;
      return {
        state: WorkflowState.LABEL_PRINTED,
        context: { ...data.context, barcode: action.barcode },
      };
    }
    case "COMPLETE": {
      if (!TRANSITIONS[data.state].has(WorkflowState.IDLE)) return data;
      return { state: WorkflowState.IDLE, context: EMPTY_CONTEXT };
    }
    case "CANCEL": {
      return { state: WorkflowState.IDLE, context: EMPTY_CONTEXT };
    }
    case "REWEIGH": {
      if (data.state !== WorkflowState.WEIGHT_CAPTURED) return data;
      return {
        state: WorkflowState.PRODUCT_SELECTED,
        context: { ...data.context, weightLb: null },
      };
    }
    default:
      return data;
  }
}

export function useWorkflow() {
  const [data, dispatch] = useReducer(workflowReducer, {
    state: WorkflowState.IDLE,
    context: EMPTY_CONTEXT,
  });

  const selectProduct = useCallback((productId: number, name: string, sku: string) => {
    dispatch({ type: "SELECT_PRODUCT", productId, name, sku });
  }, []);

  const captureWeight = useCallback((weightLb: number) => {
    dispatch({ type: "CAPTURE_WEIGHT", weightLb });
  }, []);

  const printLabel = useCallback((barcode: string) => {
    dispatch({ type: "PRINT_LABEL", barcode });
  }, []);

  const complete = useCallback(() => {
    dispatch({ type: "COMPLETE" });
  }, []);

  const cancel = useCallback(() => {
    dispatch({ type: "CANCEL" });
  }, []);

  const reweigh = useCallback(() => {
    dispatch({ type: "REWEIGH" });
  }, []);

  return {
    state: data.state,
    context: data.context,
    selectProduct,
    captureWeight,
    printLabel,
    complete,
    cancel,
    reweigh,
  };
}
