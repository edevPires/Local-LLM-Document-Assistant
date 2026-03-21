export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: number;
  conversation: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface Document {
  id: number;
  conversation: number;
  original_filename: string;
  summary: string;
  is_indexed: boolean;
  uploaded_at: string;
}
