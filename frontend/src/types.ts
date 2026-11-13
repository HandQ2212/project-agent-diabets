export type Source = { title: string; url: string; topic?: string; review_status?: string | null; fetched_at?: string | null };

export type Answer = {
  answer?: string;
  sources?: Source[];
  trace?: string[];
  score?: number;
  classification?: number;
  threshold?: number;
  topic?: string;
  disclaimer?: string;
  meaning?: string;
  model?: string;
  status?: string;
  message?: string;
  policy_overridden?: boolean;
};

export type ChatTurn = {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  trace?: string[];
  /** Thông điệp lỗi đã Việt hoá; có giá trị nghĩa là lượt này bị lỗi. */
  error?: string;
  stopped?: boolean;
  done?: boolean;
};

export type HealthStatus = {
  status: string;
  models: { symptoms: boolean; brfss: boolean; nhanes_research: boolean; nhanes15_research: boolean };
  rl: boolean;
  services?: { neo4j: boolean; ollama: boolean };
};
