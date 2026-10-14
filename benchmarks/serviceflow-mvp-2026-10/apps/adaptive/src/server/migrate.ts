import "dotenv/config";
import { defaultConfig, openDatabase, migrate } from "./database.js";
const config = defaultConfig();
const db = openDatabase(config);
await migrate(db, config);
db.close();
console.log("Migrations complete.");
