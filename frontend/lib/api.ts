import type { CompareRequest, CompareResponse, StaticData } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function compareUniversities(req: CompareRequest): Promise<CompareResponse> {
  return apiFetch<CompareResponse>("/api/compare", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function getStaticData(): Promise<StaticData> {
  return apiFetch<StaticData>("/api/static");
}
