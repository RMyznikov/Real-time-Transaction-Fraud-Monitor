export interface Transaction {
  transaction_id: string;
  account_id: string;
  amount: string;
  currency: string;
  country: string;
  timestamp: string;
}

export interface FraudAlert {
  transaction_id: string;
  account_id: string;
  rule: string;
  risk_score: number;
  created_at: string;
}

export interface PageResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface GenerateTransactionsRequest {
  valid_count: number;
  invalid_count: number;
  fraud_count: number;
}

export interface GenerationAccepted {
  status: 'accepted';
  transaction_count: number;
}

export type TransactionInput = Omit<Transaction, 'transaction_id'>;
export type FraudAlertInput = Omit<FraudAlert, 'transaction_id' | 'rule'>;
