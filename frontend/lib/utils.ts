export function safeScore(value: unknown, fallback = 0): number {
  const n = Number(value);
  if (!isFinite(n)) return fallback;
  return Math.max(0, Math.min(10, n));
}

export function scoreBar(score: unknown): string {
  const clamped = safeScore(score);
  const filled = Math.round(clamped);
  return "🟦".repeat(filled) + "⬜".repeat(10 - filled);
}

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
