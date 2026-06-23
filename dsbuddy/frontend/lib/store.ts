import { create } from "zustand";
import { normalizeResponse } from "./normalize";
import type {
  AnalyzeResponse,
  ChatMessage,
  UploadStep,
} from "./types";

interface AnalysisState {
  result: AnalyzeResponse | null;
  sessionId: string | null;
  uploadStep: UploadStep;
  setResult: (result: AnalyzeResponse, sessionId: string) => void;
  setUploadStep: (step: UploadStep) => void;
  clearResult: () => void;
}

interface ChatState {
  messages: ChatMessage[];
  messagesRemaining: number;
  isChatOpen: boolean;
  addMessage: (msg: ChatMessage) => void;
  setMessagesRemaining: (count: number) => void;
  setChatOpen: (open: boolean) => void;
  resetChat: () => void;
}

interface GraphState {
  selectedFeature: string | null;
  setSelectedFeature: (feature: string | null) => void;
}

type AppStore = AnalysisState & ChatState & GraphState;

export const useAppStore = create<AppStore>((set) => ({
  // ── Analysis ────────────────────────────────────────────────────────────────
  result: null,
  sessionId: null,
  uploadStep: "idle",

  setResult: (result, sessionId) =>
    set({ result: normalizeResponse(result), sessionId, uploadStep: "done" }),

  setUploadStep: (step) => set({ uploadStep: step }),

  clearResult: () =>
    set({ result: null, sessionId: null, uploadStep: "idle" }),

  // ── Chat ────────────────────────────────────────────────────────────────────
  messages: [],
  messagesRemaining: 3,
  isChatOpen: false,

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  setMessagesRemaining: (count) => set({ messagesRemaining: count }),

  setChatOpen: (open) => set({ isChatOpen: open }),

  resetChat: () => set({ messages: [], messagesRemaining: 3 }),

  // ── Graph ───────────────────────────────────────────────────────────────────
  selectedFeature: null,
  setSelectedFeature: (feature) => set({ selectedFeature: feature }),
}));
