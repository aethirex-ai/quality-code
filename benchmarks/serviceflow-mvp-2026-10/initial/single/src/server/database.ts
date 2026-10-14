import Database from "better-sqlite3";
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
export function openDatabase(path: string) {
  if (path !== ":memory:")
    mkdirSync(dirname(resolve(path)), { recursive: true });
  const db = new Database(path);
  db.pragma("foreign_keys = ON");
  db.pragma("journal_mode = WAL");
  db.pragma("busy_timeout = 5000");
  return db;
}
export function migrateApplication(db: Database.Database) {
  db.exec(
    "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, appliedAt TEXT NOT NULL)",
  );
  if (
    !db
      .prepare("SELECT version FROM schema_migrations WHERE version=?")
      .get("001")
  )
    db.transaction(() => {
      db.exec(readFileSync(resolve("migrations/001_application.sql"), "utf8"));
      db.prepare("INSERT INTO schema_migrations VALUES (?,?)").run(
        "001",
        new Date().toISOString(),
      );
    })();
}
