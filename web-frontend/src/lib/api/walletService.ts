// Wallet service — wraps /api/v1/accounts/*, /api/v1/card/*, /api/v1/analytics/*
import { apiFetch, TokenManager } from "./client";

// ---------------------------------------------------------------------------
// Exported types (consumed by walletSlice.ts)
// ---------------------------------------------------------------------------
export interface Account {
  id: string;
  user_id: string;
  account_number: string;
  account_type: "checking" | "savings" | "business";
  currency: string;
  balance: number;
  available_balance: number;
  status: "active" | "inactive" | "frozen" | "closed";
  daily_limit: number;
  monthly_limit: number;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  account_id: string;
  from_account_id?: string;
  to_account_id?: string;
  type:
    | "deposit"
    | "withdrawal"
    | "transfer"
    | "payment"
    | "refund"
    | "fee"
    | "reversal";
  amount: number;
  currency: string;
  status: "pending" | "completed" | "failed" | "cancelled" | "reversed";
  description?: string;
  reference?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Card {
  id: string;
  account_id: string;
  card_number_masked: string;
  card_type: "debit" | "credit" | "prepaid";
  status: "active" | "inactive" | "blocked" | "expired" | "frozen";
  expiry_month: number;
  expiry_year: number;
  cardholder_name: string;
  daily_limit: number;
  monthly_limit: number;
  contactless_enabled: boolean;
  online_enabled: boolean;
  international_enabled: boolean;
  created_at: string;
}

export interface TransactionFilters {
  page?: number;
  per_page?: number;
  type?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
}

interface AccountsResponse {
  accounts: Account[];
}

interface TransactionsResponse {
  data: Transaction[];
  total: number;
  page: number;
  per_page: number;
}

interface DashboardSummary {
  total_balance: number;
  total_accounts: number;
  total_cards: number;
  recent_transactions: Transaction[];
  monthly_spending: number;
  monthly_income: number;
}

interface SpendingAnalytics {
  total_spent: number;
  categories: Array<{ category: string; amount: number; percentage: number }>;
  trends: Array<{ date: string; amount: number }>;
}

// ---------------------------------------------------------------------------
// Demo mode helpers
// ---------------------------------------------------------------------------
const isDemoMode = (): boolean => {
  const token = TokenManager.getAccessToken();
  return token?.startsWith("demo.") ?? false;
};

const NOW = new Date().toISOString();
const D1 = new Date(Date.now() - 86_400_000).toISOString();
const D3 = new Date(Date.now() - 3 * 86_400_000).toISOString();
const D7 = new Date(Date.now() - 7 * 86_400_000).toISOString();

const DEMO_ACCOUNTS: Account[] = [
  {
    id: "demo-acc-001",
    user_id: "demo-user-001",
    account_number: "4532 •••• •••• 1234",
    account_type: "checking",
    currency: "USD",
    balance: 12_450.75,
    available_balance: 12_200.0,
    status: "active",
    daily_limit: 5_000,
    monthly_limit: 50_000,
    created_at: D7,
    updated_at: NOW,
  },
  {
    id: "demo-acc-002",
    user_id: "demo-user-001",
    account_number: "5678 •••• •••• 5678",
    account_type: "savings",
    currency: "USD",
    balance: 28_930.2,
    available_balance: 28_930.2,
    status: "active",
    daily_limit: 10_000,
    monthly_limit: 100_000,
    created_at: D7,
    updated_at: NOW,
  },
];

const DEMO_TRANSACTIONS: Transaction[] = [
  {
    id: "demo-tx-001",
    account_id: "demo-acc-001",
    type: "deposit",
    amount: 3_200.0,
    currency: "USD",
    status: "completed",
    description: "Salary — April 2026",
    created_at: D1,
    updated_at: D1,
  },
  {
    id: "demo-tx-002",
    account_id: "demo-acc-001",
    type: "payment",
    amount: 89.99,
    currency: "USD",
    status: "completed",
    description: "Netflix subscription",
    created_at: D1,
    updated_at: D1,
  },
  {
    id: "demo-tx-003",
    account_id: "demo-acc-001",
    type: "payment",
    amount: 234.5,
    currency: "USD",
    status: "completed",
    description: "Grocery store",
    created_at: D3,
    updated_at: D3,
  },
  {
    id: "demo-tx-004",
    account_id: "demo-acc-001",
    type: "transfer",
    amount: 500.0,
    currency: "USD",
    status: "completed",
    description: "Transfer to savings",
    to_account_id: "demo-acc-002",
    created_at: D3,
    updated_at: D3,
  },
  {
    id: "demo-tx-005",
    account_id: "demo-acc-001",
    type: "payment",
    amount: 45.0,
    currency: "USD",
    status: "pending",
    description: "Coffee shop",
    created_at: NOW,
    updated_at: NOW,
  },
  {
    id: "demo-tx-006",
    account_id: "demo-acc-001",
    type: "deposit",
    amount: 150.0,
    currency: "USD",
    status: "completed",
    description: "Freelance payment",
    created_at: D7,
    updated_at: D7,
  },
  {
    id: "demo-tx-007",
    account_id: "demo-acc-001",
    type: "payment",
    amount: 12.99,
    currency: "USD",
    status: "completed",
    description: "Spotify",
    created_at: D7,
    updated_at: D7,
  },
  {
    id: "demo-tx-008",
    account_id: "demo-acc-001",
    type: "payment",
    amount: 78.6,
    currency: "USD",
    status: "completed",
    description: "Electric bill",
    created_at: D7,
    updated_at: D7,
  },
];

const DEMO_CARDS: Card[] = [
  {
    id: "demo-card-001",
    account_id: "demo-acc-001",
    card_number_masked: "•••• •••• •••• 4242",
    card_type: "debit",
    status: "active",
    expiry_month: 12,
    expiry_year: 2028,
    cardholder_name: "Demo User",
    daily_limit: 2_000,
    monthly_limit: 10_000,
    contactless_enabled: true,
    online_enabled: true,
    international_enabled: false,
    created_at: D7,
  },
];

// ---------------------------------------------------------------------------
// walletService
// ---------------------------------------------------------------------------
export const walletService = {
  // ----- Accounts -----------------------------------------------------------
  async getAccounts(): Promise<Account[]> {
    if (isDemoMode()) return DEMO_ACCOUNTS;
    try {
      const data = await apiFetch<AccountsResponse>("/accounts/");
      return data.accounts ?? [];
    } catch {
      return DEMO_ACCOUNTS;
    }
  },

  async getAccount(accountId: string): Promise<Account> {
    return apiFetch<Account>(`/accounts/${accountId}`);
  },

  async createAccount(body: {
    account_type: "checking" | "savings" | "business";
    currency?: string;
  }): Promise<Account> {
    return apiFetch<Account>("/accounts/", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  // ----- Transactions -------------------------------------------------------
  async getTransactions(
    accountId: string,
    filters?: TransactionFilters,
  ): Promise<TransactionsResponse> {
    if (isDemoMode()) {
      const txs = DEMO_TRANSACTIONS.filter(
        (t) => t.account_id === accountId || accountId === "demo-acc-001",
      );
      return { data: txs, total: txs.length, page: 1, per_page: txs.length };
    }
    try {
      const params = filters
        ? "?" +
          new URLSearchParams(filters as Record<string, string>).toString()
        : "";
      return apiFetch<TransactionsResponse>(
        `/accounts/${accountId}/transactions${params}`,
      );
    } catch {
      return {
        data: DEMO_TRANSACTIONS,
        total: DEMO_TRANSACTIONS.length,
        page: 1,
        per_page: DEMO_TRANSACTIONS.length,
      };
    }
  },

  async depositFunds(body: {
    account_id: string;
    amount: number;
    description?: string;
  }): Promise<Transaction> {
    return apiFetch<Transaction>(`/accounts/${body.account_id}/deposit`, {
      method: "POST",
      body: JSON.stringify({
        amount: body.amount,
        description: body.description,
      }),
    });
  },

  async withdrawFunds(body: {
    account_id: string;
    amount: number;
    description?: string;
  }): Promise<Transaction> {
    return apiFetch<Transaction>(`/accounts/${body.account_id}/withdraw`, {
      method: "POST",
      body: JSON.stringify({
        amount: body.amount,
        description: body.description,
      }),
    });
  },

  async transferFunds(body: {
    from_account_id: string;
    to_account_id: string;
    amount: number;
    description?: string;
  }): Promise<Transaction> {
    return apiFetch<Transaction>(`/accounts/${body.from_account_id}/transfer`, {
      method: "POST",
      body: JSON.stringify({
        to_account_id: body.to_account_id,
        amount: body.amount,
        description: body.description,
      }),
    });
  },

  // ----- Cards --------------------------------------------------------------
  async getCards(): Promise<Card[]> {
    if (isDemoMode()) return DEMO_CARDS;
    try {
      const data = await apiFetch<{ cards: Card[] }>("/card/");
      return data.cards ?? [];
    } catch {
      return DEMO_CARDS;
    }
  },

  async getCard(cardId: string): Promise<Card> {
    return apiFetch<Card>(`/card/${cardId}`);
  },

  async issueCard(body: {
    account_id: string;
    card_type: "debit" | "credit" | "prepaid";
    daily_limit?: number;
    monthly_limit?: number;
  }): Promise<Card> {
    return apiFetch<Card>("/card/issue", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async activateCard(cardId: string, _activationCode: string): Promise<void> {
    await apiFetch(`/card/${cardId}/activate`, { method: "POST" });
  },

  async toggleCardStatus(
    cardId: string,
    action: "block" | "unblock",
  ): Promise<void> {
    const endpoint = action === "block" ? "freeze" : "unfreeze";
    await apiFetch(`/card/${cardId}/${endpoint}`, { method: "POST" });
  },

  // ----- Dashboard & Analytics ----------------------------------------------
  async getAccountSummary(): Promise<DashboardSummary> {
    if (isDemoMode()) {
      const totalBalance = DEMO_ACCOUNTS.reduce((s, a) => s + a.balance, 0);
      const income = DEMO_TRANSACTIONS.filter(
        (t) => t.type === "deposit",
      ).reduce((s, t) => s + t.amount, 0);
      const spending = DEMO_TRANSACTIONS.filter(
        (t) => t.type !== "deposit",
      ).reduce((s, t) => s + t.amount, 0);
      return {
        total_balance: totalBalance,
        total_accounts: DEMO_ACCOUNTS.length,
        total_cards: DEMO_CARDS.length,
        recent_transactions: DEMO_TRANSACTIONS.slice(0, 5),
        monthly_spending: spending,
        monthly_income: income,
      };
    }
    // Aggregate from accounts + cards endpoints when a dedicated summary
    // endpoint is not available
    try {
      const dash = await apiFetch<{
        summary?: Record<string, number>;
        recent_transactions?: Transaction[];
      }>("/analytics/dashboard");
      const s = dash.summary ?? {};
      return {
        total_balance: s.total_balance ?? 0,
        total_accounts: s.total_accounts ?? 0,
        total_cards: s.total_cards ?? 0,
        recent_transactions: dash.recent_transactions ?? [],
        monthly_spending: s.monthly_spending ?? 0,
        monthly_income: s.monthly_income ?? 0,
      };
    } catch {
      // Fallback: build summary from accounts list
      try {
        const accounts = await walletService.getAccounts();
        const cards = await walletService.getCards();
        const totalBalance = accounts.reduce((sum, a) => sum + a.balance, 0);
        return {
          total_balance: totalBalance,
          total_accounts: accounts.length,
          total_cards: cards.length,
          recent_transactions: [],
          monthly_spending: 0,
          monthly_income: 0,
        };
      } catch {
        return {
          total_balance: 0,
          total_accounts: 0,
          total_cards: 0,
          recent_transactions: [],
          monthly_spending: 0,
          monthly_income: 0,
        };
      }
    }
  },

  async getSpendingAnalytics(
    _accountId?: string,
    period?: "week" | "month" | "quarter" | "year",
  ): Promise<SpendingAnalytics> {
    const params = period ? `?period=${period}` : "";
    try {
      return await apiFetch<SpendingAnalytics>(`/analytics/spending${params}`);
    } catch {
      return { total_spent: 0, categories: [], trends: [] };
    }
  },
};
