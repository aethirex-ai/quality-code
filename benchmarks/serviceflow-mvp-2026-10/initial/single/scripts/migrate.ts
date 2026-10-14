import "dotenv/config";
import { getMigrations } from "better-auth/db/migration";
import { createAuth } from "../src/server/auth.js";
import { openDatabase, migrateApplication } from "../src/server/database.js";
const db = openDatabase(
  process.env.DATABASE_PATH || "./data/serviceflow.sqlite",
);
const auth = createAuth(
  db,
  "http://127.0.0.1:3000",
  "migration-only-not-a-runtime-session-secret",
  false,
  true,
);
const { runMigrations } = await getMigrations(auth.options);
await runMigrations();
migrateApplication(db);
db.close();
console.log("Better Auth and application migrations applied.");
