export enum OpenAIModel {
  DAVINCI_TURBO = "gpt-3.5-turbo"
}

export interface Message {
  role: Role;
  content: string;
  isStreaming?: boolean;
  timestamp?: number;
}

export type Role = "assistant" | "user";
