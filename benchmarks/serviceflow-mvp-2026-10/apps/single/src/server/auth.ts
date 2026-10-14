import { betterAuth } from "better-auth";
import type Database from "better-sqlite3";
export function createAuth(
  db: Database.Database,
  origin: string,
  secret: string,
  test = false,
  migrating = false,
) {
  return betterAuth({
    database: db,
    baseURL: origin,
    secret,
    trustedOrigins: [origin],
    emailAndPassword: {
      enabled: true,
      disableSignUp: true,
      minPasswordLength: 12,
    },
    session: { expiresIn: 60 * 60 * 24, cookieCache: { enabled: false } },
    rateLimit: { enabled: !test },
    advanced: {
      database: { validateSchema: !migrating },
      useSecureCookies: origin.startsWith("https://"),
      defaultCookieAttributes: { httpOnly: true, sameSite: "lax" },
    },
    logger: { level: "error" },
  });
}
export type Auth = ReturnType<typeof createAuth>;
