import express, { type ErrorRequestHandler } from "express";
import helmet from "helmet";
import { rateLimit } from "express-rate-limit";
import { fromNodeHeaders, toNodeHandler } from "better-auth/node";
import type Database from "better-sqlite3";
import { resolve } from "node:path";
import { createAuth } from "./auth.js";
import { Store, ProductError } from "./domain.js";
import { generateDraft, type AISettings } from "./ai.js";
import type { Role, User } from "../shared/contracts.js";
export interface AppOptions {
  db: Database.Database;
  origin: string;
  secret: string;
  test?: boolean;
  ai?: AISettings;
  transport?: typeof fetch;
  serveClient?: boolean;
}
export function createApp(options: AppOptions) {
  const app = express(),
    auth = createAuth(options.db, options.origin, options.secret, options.test),
    store = new Store(options.db);
  app.disable("x-powered-by");
  app.use(
    helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'"],
          styleSrc: ["'self'"],
          imgSrc: ["'self'", "data:"],
          connectSrc: ["'self'"],
          frameAncestors: ["'none'"],
        },
      },
      strictTransportSecurity: options.origin.startsWith("https://")
        ? undefined
        : false,
    }),
  );
  app.use("/api", (_req, res, next) => {
    res.set("Cache-Control", "no-store");
    next();
  });
  // Exact trusted-origin + Fetch Metadata and JSON-only mutations prevent cross-site form and fetch writes.
  app.use("/api", (req, res, next) => {
    if (!["GET", "HEAD", "OPTIONS"].includes(req.method)) {
      if (
        req.get("origin") !== options.origin ||
        req.get("sec-fetch-site") === "cross-site"
      )
        return res
          .status(403)
          .json({ error: "Cross-site or missing-origin action rejected." });
      if (!req.is("application/json"))
        return res.status(415).json({ error: "JSON is required." });
    }
    next();
  });
  // Demo accounts only; expose no signup, reset, account deletion or role-changing auth endpoint.
  const authRoutes = new Set([
    "/sign-in/email",
    "/sign-out",
    "/get-session",
    "/ok",
  ]);
  app.use("/api/auth", (req, res, next) => {
    if (!authRoutes.has(req.path))
      return res
        .status(404)
        .json({ error: "Authentication action unavailable in this demo." });
    next();
  });
  app.all("/api/auth/*splat", toNodeHandler(auth));
  app.use(express.json({ limit: "24kb" }));
  app.get("/api/health", (_req, res) => {
    options.db.prepare("SELECT 1").get();
    res.json({ ok: true });
  });
  const actor = async (req: express.Request): Promise<User> => {
    const session = await auth.api.getSession({
      headers: fromNodeHeaders(req.headers),
    });
    if (!session) throw new ProductError(401, "Please sign in to continue.");
    const row = options.db
      .prepare("SELECT role FROM user_roles WHERE userId=?")
      .get(session.user.id) as { role: Role } | undefined;
    if (!row)
      throw new ProductError(
        403,
        "This account does not have application access.",
      );
    return {
      id: session.user.id,
      name: session.user.name,
      email: session.user.email,
      role: row.role,
    };
  };
  app.get("/api/me", async (req, res) => res.json(await actor(req)));
  app.get("/api/services", (_req, res) => res.json(store.services()));
  app.get("/api/admin/services", async (req, res) => {
    const u = await actor(req);
    store.admin(u);
    res.json(store.services(u));
  });
  app.get("/api/admin/activity", async (req, res) => {
    const u = await actor(req);
    store.admin(u);
    res.json(
      options.db
        .prepare(
          "SELECT id,actorName,action,createdAt FROM activity WHERE requestId IS NULL ORDER BY id DESC LIMIT 100",
        )
        .all(),
    );
  });
  app.get("/api/requests", async (req, res) =>
    res.json(store.requests(await actor(req))),
  );
  app.get("/api/requests/:id", async (req, res) =>
    res.json(store.detail(await actor(req), String(req.params.id))),
  );
  app.post("/api/requests", async (req, res) =>
    res
      .status(201)
      .json(
        store.createRequest(
          await actor(req),
          req.body,
          req.get("idempotency-key"),
        ),
      ),
  );
  app.patch("/api/requests/:id/status", async (req, res) =>
    res.json(
      store.changeStatus(
        await actor(req),
        String(req.params.id),
        req.body,
        req.get("idempotency-key"),
      ),
    ),
  );
  const draftLimiter = rateLimit({
    windowMs: 60000,
    limit: 20,
    standardHeaders: "draft-8",
    legacyHeaders: false,
    handler: (_req, res) =>
      res
        .status(429)
        .json({ error: "Too many draft attempts. Please wait a minute." }),
  });
  app.post(
    "/api/requests/:id/draft",
    ...(options.test ? [] : [draftLimiter]),
    async (req, res) => {
      const u = await actor(req);
      store.staff(u);
      const r = store.detail(u, String(req.params.id));
      res.json(await generateDraft(r, options.ai, options.transport));
    },
  );
  app.post("/api/services", async (req, res) =>
    res
      .status(201)
      .json(
        store.createService(
          await actor(req),
          req.body,
          req.get("idempotency-key"),
        ),
      ),
  );
  app.patch("/api/services/:id", async (req, res) =>
    res.json(
      store.updateService(
        await actor(req),
        String(req.params.id),
        req.body,
        req.get("idempotency-key"),
      ),
    ),
  );
  app.delete("/api/services/:id", async (req, res) =>
    res.json(
      store.deleteService(
        await actor(req),
        String(req.params.id),
        req.body,
        req.get("idempotency-key"),
      ),
    ),
  );
  app.use("/api", (_req, res) =>
    res.status(404).json({ error: "API route not found." }),
  );
  if (options.serveClient) {
    app.use(express.static(resolve("dist/client")));
    app.get("/{*splat}", (_req, res) =>
      res.sendFile(resolve("dist/client/index.html")),
    );
  }
  const errorHandler: ErrorRequestHandler = (err, _req, res, _next) => {
    if (err instanceof ProductError) {
      res.status(err.status).json({ error: err.message, fields: err.fields });
      return;
    }
    if (err?.type === "entity.parse.failed") {
      res.status(400).json({ error: "Invalid JSON." });
      return;
    }
    if (err?.type === "entity.too.large") {
      res.status(413).json({ error: "This request is too large." });
      return;
    }
    // Do not log raw exceptions, payloads or provider errors (may contain personal data/secrets).
    res.status(500).json({
      error:
        "Something went wrong. Please try again; a retry will not duplicate a saved action.",
    });
  };
  app.use(errorHandler);
  return { app, auth, store };
}
