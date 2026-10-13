import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api/client";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.isUnauthorized)
      return "Your session has expired. Please sign in again.";
    if (error.isForbidden) return "You do not have access to this resource.";
    if (error.status === 0)
      return "The server is unreachable. Check your connection.";
    if (error.status === 503) return "This service is temporarily unavailable.";
    return error.message;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}

export function useAsyncData<T>(
  loader: () => Promise<T>,
  deps: ReadonlyArray<unknown> = [],
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await loaderRef.current();
      if (mounted.current) setData(result);
    } catch (err) {
      if (mounted.current) setError(describeError(err));
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void reload();
    return () => {
      mounted.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, reload };
}
