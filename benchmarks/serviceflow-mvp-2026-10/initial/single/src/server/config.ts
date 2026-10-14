import "dotenv/config";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { randomBytes } from "node:crypto";
import { dirname, resolve } from "node:path";
export function configuration() {
  const port = Number(process.env.PORTAL_PORT || process.env.PORT || 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535)
    throw new Error("Invalid local port.");
  const origin = process.env.PORTAL_PORT
    ? `http://127.0.0.1:${port}`
    : process.env.APP_ORIGIN || `http://127.0.0.1:${port}`;
  const databasePath = process.env.DATABASE_PATH || "./data/serviceflow.sqlite";
  const secretPath = resolve(dirname(databasePath), ".auth-secret");
  let secret = process.env.BETTER_AUTH_SECRET;
  if (!secret) {
    mkdirSync(dirname(secretPath), { recursive: true });
    if (!existsSync(secretPath))
      writeFileSync(secretPath, randomBytes(48).toString("hex"), {
        mode: 0o600,
        flag: "wx",
      });
    secret = readFileSync(secretPath, "utf8").trim();
  }
  if (secret.length < 32)
    throw new Error(
      "Authentication secret must contain at least 32 characters.",
    );
  return { port, origin, databasePath, secret };
}
