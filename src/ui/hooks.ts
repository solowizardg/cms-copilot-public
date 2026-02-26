/// <reference path="./react-shim.d.ts" />
import * as React from "react";
import { useStreamContext } from "@langchain/langgraph-sdk/react-ui";

// react-shim 在部分环境下不包含 hooks 的类型声明，这里用 any 兜底避免 TS 报错
export const useState = (React as any).useState as any;
export const useEffect = (React as any).useEffect as any;

export { useStreamContext };

export { React };
