import { createAuthClient } from "better-auth/react";
export const authClient = createAuthClient();
export class ApiError extends Error {
  constructor(
    message: string,
    public status = 0,
    public fields: Record<string, string> = {},
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch("/api" + path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch {
    throw new ApiError(
      "Connection interrupted. Try again; saved actions will not be duplicated.",
    );
  }
  let result;
  try {
    result = await response.json();
  } catch {
    // A successful status does not prove the response body reached the client.
    // The write may already be committed: mutate must retain its recovery key.
    throw new ApiError(
      "The response could not be read. Please retry; a saved action will not be duplicated.",
      response.status,
    );
  }
  if (!response.ok)
    throw new ApiError(
      result?.error || "This action could not be completed.",
      response.status,
      result?.fields,
    );
  return result as T;
}
export async function mutate<T>(
  owner: string,
  path: string,
  method: string,
  body: unknown,
): Promise<T> {
  const slot = "mutation:" + owner + ":" + method + ":" + path;
  const payload = JSON.stringify(body);
  let previous: { payload: string; key: string } | undefined;
  try {
    previous = JSON.parse(sessionStorage.getItem(slot) || "null") || undefined;
  } catch {
    /* Recover a malformed local retry record. */
  }
  const record =
    previous?.payload === payload
      ? previous
      : { payload, key: crypto.randomUUID() };
  sessionStorage.setItem(slot, JSON.stringify(record));
  const result = await api<T>(path, {
    method,
    body: payload,
    headers: { "Idempotency-Key": record.key },
  });
  sessionStorage.removeItem(slot);
  return result;
}
