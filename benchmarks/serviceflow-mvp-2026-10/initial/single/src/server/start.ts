import { configuration } from "./config.js";
import { openDatabase } from "./database.js";
import { createApp } from "./app.js";
const config = configuration(),
  db = openDatabase(config.databasePath);
if (
  !db
    .prepare(
      "SELECT name FROM sqlite_master WHERE type='table' AND name='requests'",
    )
    .get()
)
  throw new Error(
    "Run npm run db:migrate and npm run db:seed before starting.",
  );
const { app } = createApp({
  db,
  origin: config.origin,
  secret: config.secret,
  serveClient: true,
  ai: { key: process.env.AI_API_KEY, model: process.env.AI_MODEL },
});
start(app);
function start(application: typeof app) {
  const server = application.listen(config.port, "127.0.0.1", () =>
    console.log(`ServiceFlow running at ${config.origin}`),
  );
  server.on("error", () => {
    console.error("Unable to bind the configured local port.");
    process.exitCode = 1;
    db.close();
  });
  for (const signal of ["SIGINT", "SIGTERM"] as const)
    process.on(signal, () =>
      server.close(() => {
        db.close();
        process.exit(0);
      }),
    );
}
