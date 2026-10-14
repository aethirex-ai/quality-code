import { spawn, execFileSync, type ChildProcess } from "node:child_process";
import { createServer } from "node:net";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
const directory = mkdtempSync(join(tmpdir(), "serviceflow-fresh-"));
const allocator = createServer();
await new Promise<void>((resolve, reject) => {
  allocator.once("error", reject);
  allocator.listen(0, "127.0.0.1", resolve);
});
const port = (allocator.address() as { port: number }).port;
await new Promise<void>((resolve) => allocator.close(() => resolve()));
const origin = `http://127.0.0.1:${port}`,
  env = {
    ...process.env,
    PORTAL_PORT: String(port),
    APP_ORIGIN: "",
    DATABASE_PATH: join(directory, "fresh.sqlite"),
    BETTER_AUTH_SECRET: "",
    AI_API_KEY: "",
    AI_MODEL: "",
    NODE_ENV: "production",
  };
let server: ChildProcess | undefined,
  output = "";
async function start(development = false) {
  output = "";
  server = spawn(
    process.execPath,
    development
      ? ["--import", "tsx", "src/server/start.ts"]
      : ["dist/server/start.js"],
    {
      env: { ...env, NODE_ENV: development ? "development" : "production" },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  server.stdout?.on("data", (v) => (output += v));
  server.stderr?.on("data", (v) => (output += v));
  for (let i = 0; i < 80; i++) {
    if (server.exitCode !== null)
      throw new Error("Fresh server exited before ready: " + output);
    try {
      if ((await fetch(origin + "/api/health")).ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("Fresh server did not become ready.");
}
async function stop() {
  const child = server;
  if (!child || child.exitCode !== null) return;
  await new Promise<void>((resolve, reject) => {
    const timer = setTimeout(() => {
      child.kill("SIGKILL");
      reject(new Error("Owned server failed to stop."));
    }, 5000);
    child.once("exit", () => {
      clearTimeout(timer);
      resolve();
    });
    child.kill("SIGTERM");
  });
  server = undefined;
}
async function api(
  path: string,
  method = "GET",
  body?: unknown,
  cookie = "",
  key = randomUUID(),
) {
  const response = await fetch(origin + "/api" + path, {
    method,
    headers: {
      Origin: origin,
      "Content-Type": "application/json",
      Cookie: cookie,
      "Idempotency-Key": key,
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  return { response, data: await response.json() };
}
async function signIn(email: string) {
  const r = await api("/auth/sign-in/email", "POST", {
    email,
    password: "ServiceFlow2026!",
  });
  assert.equal(r.response.status, 200);
  return r.response.headers
    .getSetCookie()
    .map((s) => s.split(";")[0])
    .join("; ");
}
try {
  for (const script of ["migrate", "seed", "migrate", "seed"])
    execFileSync(
      process.execPath,
      ["--import", "tsx", "scripts/" + script + ".ts"],
      { env, stdio: "pipe" },
    );
  await start();
  assert.equal((await fetch(origin)).status, 200);
  const customer = await signIn("alex@demo.local"),
    provider = await signIn("provider@demo.local"),
    other = await signIn("jamie@demo.local");
  const date = new Date();
  date.setUTCDate(date.getUTCDate() + 10);
  const input = {
      serviceId: "small-repairs",
      description: "Fresh process test: two loose kitchen hinges.",
      location: "BS3 1AB",
      preferredFrom: date.toISOString().slice(0, 10),
      preferredTo: "",
      contactName: "Alex Morgan",
      contactEmail: "alex@demo.local",
      contactPhone: "07700 900123",
    },
    key = randomUUID();
  const created = await api("/requests", "POST", input, customer, key);
  assert.equal(created.response.status, 201);
  const id = created.data.id;
  const updated = await api(
    "/requests/" + id + "/status",
    "PATCH",
    { status: "Reviewing", version: 0 },
    provider,
  );
  assert.equal(updated.response.status, 200);
  assert.equal(updated.data.history.length, 2);
  await stop();
  await start();
  assert.equal(
    (await api("/me", "GET", undefined, customer)).response.status,
    200,
  );
  const persisted = await api("/requests/" + id, "GET", undefined, customer);
  assert.equal(persisted.data.status, "Reviewing");
  assert.equal(persisted.data.history.length, 2);
  assert.equal(persisted.data.history[1].actorName, "Sam Green");
  assert.equal(
    (await api("/requests/" + id, "GET", undefined, other)).response.status,
    404,
  );
  const retried = await api("/requests", "POST", input, customer, key);
  assert.equal(retried.data.id, id);
  const requests = await api("/requests", "GET", undefined, provider);
  assert.equal(
    requests.data.filter((r: { id: string }) => r.id === id).length,
    1,
  );
  await stop();
  await start(true);
  const devPage = await fetch(origin);
  const devHtml = await devPage.text();
  assert.ok(
    devHtml.includes("/assets/"),
    "Source development server serves the built client.",
  );
  assert.ok(
    devPage.headers
      .get("content-security-policy")
      ?.includes("script-src 'self'"),
  );
  assert.equal(
    (await api("/me", "GET", undefined, customer)).response.status,
    200,
  );
  console.log(
    "Fresh DB: migrations/seed repeated, production assets, mature auth, customer submission/provider update, real process restart, persisted session/history/ownership/retry, and source development serving all passed.",
  );
} finally {
  await stop();
  rmSync(directory, { recursive: true, force: true });
}
