import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/client", async () => {
  const actual =
    await vi.importActual<typeof import("@/lib/api/client")>(
      "@/lib/api/client",
    );
  return {
    ...actual,
    apiClient: { get: vi.fn(), post: vi.fn() },
  };
});

import { ApiError, apiClient } from "@/lib/api/client";
import { describeError } from "@/hooks/useAsyncData";
import { mlService } from "@/lib/api/mlService";

describe("mlService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("posts chat queries with the session id", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ response: "ok" });
    await mlService.chat("hello", "session-1");
    expect(apiClient.post).toHaveBeenCalledWith("/ai/chatbot/query", {
      query: "hello",
      session_id: "session-1",
    });
  });

  it("builds alert queries without empty parameters", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ alerts: [] });
    await mlService.listAlerts({ per_page: 50, status: undefined });
    expect(apiClient.get).toHaveBeenCalledWith(
      "/ai/fraud-detection/alerts?per_page=50",
    );
  });

  it("sends alert responses to the owner endpoint", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({});
    await mlService.respondToAlert("a1", "not_me");
    expect(apiClient.post).toHaveBeenCalledWith(
      "/ai/fraud-detection/alerts/a1/respond",
      { response: "not_me" },
    );
  });

  it("requests spending analysis for a period", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ analysis: {} });
    await mlService.spendingAnalysis(30);
    expect(apiClient.get).toHaveBeenCalledWith("/ai/spending/analysis?days=30");
  });
});

describe("describeError", () => {
  it("maps authorization failures to friendly messages", () => {
    expect(describeError(new ApiError("x", 401))).toContain("sign in");
    expect(describeError(new ApiError("x", 403))).toContain("access");
    expect(describeError(new ApiError("x", 503))).toContain("unavailable");
  });

  it("falls back to the error message", () => {
    expect(describeError(new Error("boom"))).toBe("boom");
    expect(describeError("weird")).toBe("Something went wrong.");
  });
});
