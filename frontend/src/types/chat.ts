/**
 * Chat types — mirrored from backend Pydantic schema to prevent drift.
 */

export interface ChatQueryIn {
  question: string;
}

export interface ChatSource {
  file_name: string;
  document_id: number;
  clause_num?: string | null;
}

export interface ChatQueryOut {
  answer: string;
  found: boolean;
  sources: ChatSource[];
}

export interface ChatMessage {
  role: 'user' | 'bot';
  text: string | null;
  source?: ChatSource | null;
  notFound?: boolean;
  isError?: boolean;
  loading?: boolean;
}
