import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(
  amount: number,
  currency = "USD",
  locale = "en-US",
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(
  date: string | Date,
  options?: Intl.DateTimeFormatOptions,
): string {
  // Normalise to a YYYY-MM-DD string for relative-day comparison
  const inputStr =
    typeof date === "string"
      ? date.slice(0, 10)
      : date.toISOString().slice(0, 10);
  const todayStr = new Date().toISOString().slice(0, 10);

  if (!options) {
    if (inputStr === todayStr) return "Today";
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    if (inputStr === yesterday.toISOString().slice(0, 10)) return "Yesterday";
  }

  // Parse date at local midnight to avoid off-by-one from UTC interpretation
  const [year, month, day] = inputStr.split("-").map(Number);
  const d = new Date(year, month - 1, day);
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    ...options,
  }).format(d);
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return formatDate(d);
}

export function formatNumber(value: number, decimals?: number): string {
  // When explicit decimals requested keep legacy formatted behaviour
  if (decimals !== undefined) {
    return new Intl.NumberFormat("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  }
  // Smart K/M notation
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1_000_000) {
    const n = abs / 1_000_000;
    const s = parseFloat(n.toFixed(2)).toString();
    return `${sign}${s}M`;
  }
  if (abs >= 1_000) {
    const n = abs / 1_000;
    const s = parseFloat(n.toFixed(2)).toString();
    return `${sign}${s}K`;
  }
  return `${sign}${parseFloat(abs.toFixed(2)).toString()}`;
}

export function formatPercentage(value: number, decimals = 1): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(decimals)}%`;
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 3) + "...";
}

export function maskCardNumber(cardNumber: string): string {
  const last4 = cardNumber.slice(-4);
  return `•••• •••• •••• ${last4}`;
}

export function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number,
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function isValidPhone(phone: string): boolean {
  return /^\+?[1-9]\d{1,14}$/.test(phone.replace(/[\s\-()]/g, ""));
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) {
    // Single word - use first two characters
    const word = parts[0];
    return (word[0] + (word[1] ?? "")).toUpperCase();
  }
  return parts
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}

export function slugify(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function omit<T extends Record<string, unknown>>(
  obj: T,
  keys: (keyof T)[],
): Partial<T> {
  const result = { ...obj };
  for (const key of keys) delete result[key];
  return result;
}

export function pick<T extends Record<string, unknown>>(
  obj: T,
  keys: (keyof T)[],
): Partial<T> {
  const result: Partial<T> = {};
  for (const key of keys) {
    if (key in obj) result[key] = obj[key];
  }
  return result;
}
