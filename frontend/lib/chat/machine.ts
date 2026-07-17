/**
 * Chat state machine — pure logic, no React/no network (unit-tested).
 * Guarantees (F1-01/02/06): one in-flight message at a time; retry keeps the user
 * message (no duplicates); done gates the CTA; mode switch after the first user
 * answer requires an explicit RESET_MODE (page asks confirmation first).
 */
import type { ChatResponse, JourneyMode, Phase, Profile } from "@/types";

export interface ChatMessage {
  role: "ai" | "user";
  text: string;
}

export interface ChatState {
  mode: JourneyMode;
  messages: ChatMessage[];
  profile: Profile | null;
  phase: Phase | null;
  pending: boolean;
  error: boolean;
  done: boolean;
  /** Text of the message awaiting a server reply — kept for RETRY after FAIL. */
  lastUserText: string | null;
  /** True once the user has sent at least one answer (mode switch needs confirm). */
  userAnswered: boolean;
}

export type ChatAction =
  | { type: "OPEN" } // request the opening AI turn
  | { type: "SEND"; text: string }
  | { type: "RECEIVE"; res: ChatResponse }
  | { type: "FAIL" }
  | { type: "RETRY" }
  | { type: "RESET_MODE"; mode: JourneyMode }
  | { type: "PROFILE_PATCHED"; profile: Profile };

export function initialChatState(mode: JourneyMode): ChatState {
  return {
    mode, messages: [], profile: null, phase: null,
    pending: false, error: false, done: false,
    lastUserText: null, userAnswered: false,
  };
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "OPEN":
      return { ...state, pending: true, error: false, lastUserText: null };

    case "SEND": {
      const text = action.text.trim();
      if (!canSend(state, text)) return state;
      return {
        ...state,
        messages: [...state.messages, { role: "user", text }],
        pending: true, error: false, lastUserText: text, userAnswered: true,
      };
    }

    case "RECEIVE":
      return {
        ...state,
        messages: [...state.messages, { role: "ai", text: action.res.reply }],
        profile: action.res.profile,
        phase: action.res.phase,
        done: action.res.done,
        pending: false, error: false, lastUserText: null,
      };

    case "FAIL":
      return { ...state, pending: false, error: true };

    case "RETRY":
      // Re-submit lastUserText (page re-calls the API) WITHOUT appending a duplicate bubble.
      if (state.lastUserText === null && state.messages.length > 0) return state;
      return { ...state, pending: true, error: false };

    case "RESET_MODE":
      return initialChatState(action.mode);

    case "PROFILE_PATCHED":
      return { ...state, profile: action.profile };

    default:
      return state;
  }
}

/** One message at a time + no empty sends + no sends after done. */
export function canSend(state: ChatState, text: string): boolean {
  return !state.pending && !state.done && !state.error && text.trim().length > 0;
}

/** Mode is freely changeable until the user has actually answered (F1-01). */
export function canChangeModeFreely(state: ChatState): boolean {
  return !state.userAnswered;
}
