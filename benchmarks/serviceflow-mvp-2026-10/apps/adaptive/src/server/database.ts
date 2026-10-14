import { DatabaseSync } from "node:sqlite";
import { mkdirSync, readFileSync, existsSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { randomBytes } from "node:crypto";
import { betterAuth } from "better-auth";
import { getMigrations } from "better-auth/db/migration";
export interface Config {
  databasePath: string;
  baseURL: string;
  secret?: string;
  aiKey?: string;
  aiURL?: string;
  aiModel?: string;
  aiFetch?: typeof fetch;
}
export function defaultConfig(): Config {
  return {
    databasePath: resolve(
      process.env.DATABASE_PATH || "data/serviceflow.sqlite",
    ),
    baseURL:
      process.env.BETTER_AUTH_URL ||
      `http://127.0.0.1:${process.env.PORTAL_PORT || process.env.PORT || "3000"}`,
    secret: process.env.BETTER_AUTH_SECRET,
    aiKey: process.env.AI_API_KEY,
    aiURL: process.env.AI_API_URL,
    aiModel: process.env.AI_MODEL,
  };
}
export function openDatabase(config: Config) {
  mkdirSync(dirname(config.databasePath), { recursive: true });
  const db = new DatabaseSync(config.databasePath);
  db.exec(
    "PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;",
  );
  return db;
}
export function authOptions(db: DatabaseSync, config: Config, seed = false) {
  let secret = config.secret;
  if (!secret) {
    const path = config.databasePath + ".secret";
    if (!existsSync(path))
      writeFileSync(path, randomBytes(48).toString("hex"), {
        mode: 0o600,
        flag: "wx",
      });
    secret = readFileSync(path, "utf8");
  }
  return {
    database: db,
    baseURL: config.baseURL,
    secret,
    trustedOrigins: [config.baseURL],
    emailAndPassword: { enabled: true, disableSignUp: !seed },
    user: {
      additionalFields: {
        role: {
          type: ["customer", "provider", "admin"] as (
            "customer" | "provider" | "admin"
          )[],
          defaultValue: "customer",
          required: true,
          input: false,
        },
      },
    },
    session: { cookieCache: { enabled: false } },
    advanced: {
      defaultCookieAttributes: { sameSite: "lax" as const, httpOnly: true },
    },
  };
}
export async function migrate(db: DatabaseSync, config: Config) {
  const migration = await getMigrations(authOptions(db, config));
  await migration.runMigrations();
  db.exec(
    "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, appliedAt TEXT NOT NULL)",
  );
  for (const [version, file] of [
    ["001", "001-domain.sql"],
    ["002", "002-catalogue-activity.sql"],
  ])
    if (
      !db
        .prepare("SELECT version FROM schema_migrations WHERE version=?")
        .get(version!)
    ) {
      db.exec("BEGIN IMMEDIATE");
      try {
        db.exec(readFileSync(resolve("migrations", file!), "utf8"));
        db.prepare("INSERT INTO schema_migrations VALUES (?,?)").run(
          version!,
          new Date().toISOString(),
        );
        db.exec("COMMIT");
      } catch (e) {
        db.exec("ROLLBACK");
        throw e;
      }
    }
}
export async function seedDatabase(
  db: DatabaseSync,
  config: Config,
  examples = true,
) {
  const auth = betterAuth(authOptions(db, config, true));
  for (const [email, name, role] of [
    ["customer@serviceflow.demo", "Jamie Morgan", "customer"],
    ["customer2@serviceflow.demo", "Alex Bennett", "customer"],
    ["provider@serviceflow.demo", "Sam Taylor", "provider"],
    ["admin@serviceflow.demo", "Robin Ellis", "admin"],
  ]) {
    if (!db.prepare("SELECT id FROM user WHERE email=?").get(email!)) {
      const result = await auth.api.signUpEmail({
        body: { email: email!, name: name!, password: "DemoHome2026!" },
      });
      db.prepare("UPDATE user SET role=? WHERE id=?").run(
        role!,
        result.user.id,
      );
    }
  }
  const insert = db.prepare(
    "INSERT OR IGNORE INTO services(id,name,description,price,active,version) VALUES (?,?,?,?,1,1)",
  );
  for (const s of [
    [
      "plumbing-repairs",
      "Plumbing repairs",
      "Leaking taps, blocked sinks and small plumbing fixes.",
      "From £65",
    ],
    [
      "home-maintenance",
      "Home maintenance",
      "A helping hand with repairs and your home to-do list.",
      "From £45",
    ],
    [
      "garden-care",
      "Garden care",
      "Seasonal tidy-ups, lawn care and hedge trimming.",
      "From £55",
    ],
    [
      "painting-decorating",
      "Painting & decorating",
      "Freshen up a room with careful preparation and a clean finish.",
      "Request a quote",
    ],
  ])
    insert.run(...s);
  if (examples) seedRequests(db);
}

export function seedRequests(db: DatabaseSync) {
  if (db.prepare("SELECT id FROM requests LIMIT 1").get()) return;
  const customer = db
    .prepare("SELECT id,name FROM user WHERE email='customer@serviceflow.demo'")
    .get() as { id: string; name: string };
  const customer2 = db
    .prepare(
      "SELECT id,name FROM user WHERE email='customer2@serviceflow.demo'",
    )
    .get() as { id: string; name: string };
  const provider = db
    .prepare("SELECT id,name FROM user WHERE email='provider@serviceflow.demo'")
    .get() as { id: string; name: string };
  const cases = [
    [
      "plumbing-repairs",
      "The bathroom tap drips throughout the night. Please inspect and replace the washer if needed.",
      "New",
    ],
    [
      "home-maintenance",
      "Two interior doors catch on their frames and a curtain rail needs fitting.",
      "Reviewing",
    ],
    [
      "garden-care",
      "Our small back garden needs a seasonal tidy and the hedge needs trimming.",
      "Quoted",
    ],
    [
      "painting-decorating",
      "We would like the living room walls refreshed in a light neutral colour.",
      "Booked",
    ],
    [
      "plumbing-repairs",
      "The kitchen mixer tap needs replacing with a new tap already purchased.",
      "Completed",
    ],
    [
      "garden-care",
      "We need help clearing overgrown shrubs at the back of the garden.",
      "Declined",
    ],
    [
      "home-maintenance",
      "A shelf needs securing and the hallway skirting board needs a small repair.",
      "New",
    ],
    [
      "painting-decorating",
      "Please quote to repaint the walls of a small home office.",
      "Reviewing",
    ],
  ];
  db.exec("BEGIN IMMEDIATE");
  try {
    cases.forEach(([serviceId, description, status], i) => {
      const c = i < 6 ? customer : customer2;
      const svc = db
        .prepare("SELECT * FROM services WHERE id=?")
        .get(serviceId!)!;
      const id = "demo-request-" + (i + 1);
      const createdAt = new Date(Date.now() - (9 - i) * 86400000).toISOString();
      const path =
        status === "Declined"
          ? ["New", "Reviewing", "Declined"]
          : ["New", "Reviewing", "Quoted", "Booked", "Completed"].slice(
              0,
              ["New", "Reviewing", "Quoted", "Booked", "Completed"].indexOf(
                status!,
              ) + 1,
            );
      const updatedAt = new Date(
        new Date(createdAt).valueOf() + (path.length - 1) * 3600000,
      ).toISOString();
      const preferredDate = new Date(Date.now() + (7 + i) * 86400000)
        .toISOString()
        .slice(0, 10);
      db.prepare(
        "INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
      ).run(
        id,
        c.id,
        serviceId!,
        String(svc.name),
        String(svc.price),
        description!,
        "Bristol BS1 (fictional)",
        preferredDate,
        null,
        c.name,
        i < 6 ? "jamie@example.test" : "alex@example.test",
        i < 6 ? "07700 900123" : "07700 900456",
        status!,
        path.length,
        createdAt,
        updatedAt,
      );
      path.forEach((state, j) =>
        db
          .prepare("INSERT INTO activity VALUES (?,?,?,?,?,?)")
          .run(
            "demo-activity-" + i + "-" + j,
            id,
            j === 0 ? c.id : provider.id,
            j === 0 ? c.name : provider.name,
            j === 0
              ? "Request submitted"
              : `Status changed from ${path[j - 1]} to ${state}`,
            new Date(new Date(createdAt).valueOf() + j * 3600000).toISOString(),
          ),
      );
    });
    db.exec("COMMIT");
  } catch (e) {
    db.exec("ROLLBACK");
    throw e;
  }
}
