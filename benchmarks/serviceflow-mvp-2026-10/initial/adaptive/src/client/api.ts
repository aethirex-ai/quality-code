import type { ApiErrorBody } from "../shared/contracts";
export class ApiError extends Error {
  constructor(
    public status: number,
    public body: ApiErrorBody,
  ) {
    super(body.error);
  }
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const data = await response.json().catch(() => ({
    error: "The server returned an unexpected response. Please try again.",
  }));
  if (!response.ok)
    throw new ApiError(response.status, {
      error:
        data.error || data.message || "Something went wrong. Please try again.",
      fields: data.fields,
    });
  return data as T;
}
export function mutationOptions(
  method: string,
  data: unknown,
  key?: string,
): RequestInit {
  return {
    method,
    body: JSON.stringify(data),
    headers: key ? { "Idempotency-Key": key } : {},
  };
}
