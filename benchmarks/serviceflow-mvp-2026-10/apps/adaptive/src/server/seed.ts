import "dotenv/config";
import {
  defaultConfig,
  openDatabase,
  migrate,
  seedDatabase,
} from "./database.js";
const config = defaultConfig();
const db = openDatabase(config);
await migrate(db, config);
await seedDatabase(db, config);
db.close();
console.log("Synthetic demo accounts and catalogue ready.");
