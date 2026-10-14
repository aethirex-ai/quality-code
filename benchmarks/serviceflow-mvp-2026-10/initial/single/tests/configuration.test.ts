import { afterEach, it, expect, vi } from "vitest";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { configuration } from "../src/server/config";
let directory: string | undefined;
afterEach(() => {
  vi.unstubAllEnvs();
  if (directory) rmSync(directory, { recursive: true, force: true });
  directory = undefined;
});
it("PORTAL_PORT overrides copied example origin and creates a stable local secret", () => {
  directory = mkdtempSync(join(tmpdir(), "serviceflow-config-"));
  vi.stubEnv("DATABASE_PATH", join(directory, "app.sqlite"));
  vi.stubEnv("BETTER_AUTH_SECRET", "");
  vi.stubEnv("PORTAL_PORT", "43210");
  vi.stubEnv("APP_ORIGIN", "http://127.0.0.1:3000");
  const first = configuration();
  expect(first.origin).toBe("http://127.0.0.1:43210");
  expect(first.port).toBe(43210);
  expect(first.secret.length).toBeGreaterThanOrEqual(32);
  expect(configuration().secret).toBe(first.secret);
});
it("rejects invalid port and short configured secret", () => {
  vi.stubEnv("PORTAL_PORT", "-1");
  expect(() => configuration()).toThrow("port");
  vi.stubEnv("PORTAL_PORT", "3000");
  vi.stubEnv("BETTER_AUTH_SECRET", "short");
  expect(() => configuration()).toThrow("secret");
});
