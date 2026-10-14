import "dotenv/config";
import express from "express";
import helmet from "helmet";
import { resolve } from "node:path";
import { createApp } from "./app.js";
import { defaultConfig } from "./database.js";
const config = defaultConfig();
const { app } = await createApp(config);
if (process.argv.includes("--production")) {
  app.use(
    helmet.contentSecurityPolicy({
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'"],
        imgSrc: ["'self'", "data:"],
        fontSrc: ["'self'"],
        connectSrc: ["'self'"],
        objectSrc: ["'none'"],
        frameAncestors: ["'none'"],
        upgradeInsecureRequests: null,
      },
    }),
  );
  app.use(express.static(resolve("dist/client")));
  app.get("/{*path}", (_req, res) =>
    res.sendFile(resolve("dist/client/index.html")),
  );
} else {
  const { createServer } = await import("vite");
  const vite = await createServer({
    server: { middlewareMode: true },
    appType: "spa",
  });
  app.use(vite.middlewares);
}
const port = Number(process.env.PORTAL_PORT || process.env.PORT || 3000);
if (!Number.isInteger(port) || port < 1 || port > 65535)
  throw new Error("Invalid configured port");
const server = app.listen(port, "127.0.0.1", () =>
  console.log(`ServiceFlow available at ${config.baseURL}`),
);
server.on("error", () => {
  console.error("Could not bind configured application port.");
  process.exit(1);
});
