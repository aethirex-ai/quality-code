import { beforeAll, afterAll, it, expect, vi } from "vitest";
import { createServer } from "node:http";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { getMigrations } from "better-auth/db/migration";
import { openDatabase, migrateApplication } from "../src/server/database";
import { createApp } from "../src/server/app";
import { seedDatabase, DEMO_PASSWORD } from "../scripts/seed-data";
import { mutate, ApiError } from "../src/client/api";
import type { RequestDetail } from "../src/shared/contracts";

const nativeFetch = globalThis.fetch;
const directory = mkdtempSync(join(tmpdir(), "serviceflow-body-recovery-"));
const db = openDatabase(join(directory, "app.sqlite"));
let app: ReturnType<typeof createApp>["app"];
let interruptNextCommittedResponse = true;
let interruptedStatus = 0;
const server = createServer((request, response) => {
  const end = response.end;
  response.end = ((...args: unknown[]) => {
    if (
      request.method === "POST" &&
      request.url === "/api/requests" &&
      response.statusCode === 201 &&
      interruptNextCommittedResponse
    ) {
      interruptNextCommittedResponse = false;
      interruptedStatus = response.statusCode;
      // The real application has already committed its request/history transaction.
      // Send real successful headers but truncate the actual HTTP response body.
      response.flushHeaders();
      response.write('{"id":');
      setTimeout(() => response.destroy(), 20);
      return response;
    }
    return Reflect.apply(end, response, args);
  }) as typeof response.end;
  app(request, response);
});
let origin: string;
let cookie: string;
beforeAll(async () => {
  const { runMigrations } = await getMigrations({
    database: db,
    advanced: { database: { validateSchema: false } },
  });
  await runMigrations();
  migrateApplication(db);
  await seedDatabase(db);
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  origin = `http://127.0.0.1:${(server.address() as { port: number }).port}`;
  app = createApp({
    db,
    origin,
    secret: "synthetic-response-recovery-test-secret-32-chars",
    test: true,
  }).app;
  const signedIn = await nativeFetch(origin + "/api/auth/sign-in/email", {
    method: "POST",
    headers: { Origin: origin, "Content-Type": "application/json" },
    body: JSON.stringify({ email: "alex@demo.local", password: DEMO_PASSWORD }),
  });
  expect(signedIn.status).toBe(200);
  cookie = signedIn.headers
    .getSetCookie()
    .map((value) => value.split(";")[0])
    .join("; ");
  await signedIn.arrayBuffer();
});
afterAll(async () => {
  vi.unstubAllGlobals();
  server.closeIdleConnections();
  await new Promise<void>((resolve, reject) =>
    server.close((error) => (error ? reject(error) : resolve())),
  );
  db.close();
  rmSync(directory, { recursive: true, force: true });
});
it("AUD-001: preserves the key after a real committed 201 body is interrupted; retry creates exactly one request/history entry", async () => {
  const values = new Map<string, string>();
  vi.stubGlobal("sessionStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
  });
  const keys: string[] = [];
  vi.stubGlobal("fetch", async (input: string, options: RequestInit) => {
    const headers = new Headers(options.headers);
    headers.set("Origin", origin);
    headers.set("Cookie", cookie);
    keys.push(headers.get("Idempotency-Key")!);
    return nativeFetch(new URL(input, origin), { ...options, headers });
  });
  const date = new Date();
  date.setUTCDate(date.getUTCDate() + 10);
  const body = {
    serviceId: "small-repairs",
    description: "Interrupted response recovery: two kitchen hinges.",
    location: "BS3 1AB",
    preferredFrom: date.toISOString().slice(0, 10),
    preferredTo: "",
    contactName: "Alex Morgan",
    contactEmail: "alex@demo.local",
    contactPhone: "07700 900123",
  };
  let failure: unknown;
  try {
    await mutate<RequestDetail>("demo-alex", "/requests", "POST", body);
  } catch (error) {
    failure = error;
  }
  const pending = values.get("mutation:demo-alex:POST:/requests");
  const result = await mutate<RequestDetail>(
    "demo-alex",
    "/requests",
    "POST",
    body,
  );
  const committed = db
    .prepare("SELECT id FROM requests WHERE description=?")
    .all(body.description) as { id: string }[];
  expect(interruptedStatus).toBe(201);
  expect(committed).toHaveLength(1);
  expect(failure).toBeInstanceOf(ApiError);
  expect(pending).toBeDefined();
  expect(JSON.parse(pending!)).toEqual({
    key: keys[0],
    payload: JSON.stringify(body),
  });
  expect(keys).toEqual([keys[0], keys[0]]);
  expect(result.id).toBe(committed[0].id);
  expect(
    db
      .prepare("SELECT COUNT(*) AS total FROM activity WHERE requestId=?")
      .get(result.id),
  ).toEqual({ total: 1 });
  expect(values.size).toBe(0);
});
