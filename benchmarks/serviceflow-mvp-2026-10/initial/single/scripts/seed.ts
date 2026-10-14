import "dotenv/config";
import { openDatabase } from "../src/server/database.js";
import { seedDatabase } from "./seed-data.js";
const db = openDatabase(
  process.env.DATABASE_PATH || "./data/serviceflow.sqlite",
);
await seedDatabase(db);
db.close();
console.log(
  "Seeded four synthetic demo accounts, four services and six enquiries; existing data preserved.",
);
