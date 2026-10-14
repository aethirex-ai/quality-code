import express, {
  type Request,
  type Response,
  type NextFunction,
} from "express";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import { betterAuth } from "better-auth";
import { toNodeHandler, fromNodeHeaders } from "better-auth/node";
import { randomUUID } from "node:crypto";
import { z } from "zod";
import { openDatabase, authOptions, migrate, type Config } from "./database.js";
import { makeDraft } from "./drafts.js";
import {
  STATUSES,
  type ServiceRequest,
  type User,
  type Service,
} from "../shared/contracts.js";
class HttpError extends Error {
  constructor(
    public code: number,
    message: string,
  ) {
    super(message);
  }
}
const text = (min: number, max: number) => z.string().trim().min(min).max(max);
const date = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/)
  .refine((v) => {
    const d = new Date(v + "T00:00:00Z");
    return !Number.isNaN(d.valueOf()) && d.toISOString().slice(0, 10) === v;
  }, "Enter a valid calendar date");
const requestSchema = z
  .object({
    serviceId: text(1, 100),
    description: text(10, 2000),
    location: text(3, 180),
    preferredDate: date,
    preferredEndDate: date.optional().or(z.literal("")),
    contactName: text(2, 100),
    contactEmail: z.string().trim().toLowerCase().email().max(254),
    contactPhone: text(7, 40)
      .regex(/^[+\d ()-]+$/)
      .refine(
        (v) => (v.match(/\d/g) || []).length >= 7,
        "Enter a valid phone number",
      ),
  })
  .strict()
  .superRefine((v, c) => {
    if (v.preferredDate < new Date().toISOString().slice(0, 10))
      c.addIssue({
        code: "custom",
        path: ["preferredDate"],
        message: "Choose today or a future date",
      });
    if (v.preferredEndDate && v.preferredEndDate < v.preferredDate)
      c.addIssue({
        code: "custom",
        path: ["preferredEndDate"],
        message: "End date must be on or after start date",
      });
  });
const serviceSchema = z
  .object({
    name: text(3, 100),
    description: text(10, 700),
    price: text(2, 100),
    active: z.boolean(),
    version: z.number().int().positive().optional(),
  })
  .strict();
const transitionSchema = z
  .object({ status: z.enum(STATUSES), version: z.number().int().positive() })
  .strict();
export async function createApp(config: Config) {
  const db = openDatabase(config);
  await migrate(db, config);
  const auth = betterAuth(authOptions(db, config));
  const app = express();
  app.disable("x-powered-by");
  app.use("/api", (_req, res, next) => {
    res.set("Cache-Control", "no-store");
    next();
  });
  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(
    "/api",
    rateLimit({
      windowMs: 60000,
      limit: 180,
      standardHeaders: "draft-8",
      legacyHeaders: false,
      message: { error: "Too many requests. Please try again shortly." },
    }),
  );
  app.all("/api/auth/{*path}", toNodeHandler(auth));
  app.use("/api", express.json({ limit: "24kb" }));
  app.use("/api", (req, res, next) => {
    if (!["GET", "HEAD", "OPTIONS"].includes(req.method)) {
      if (
        req.get("origin") !== new URL(config.baseURL).origin ||
        !req.is("application/json")
      )
        return res
          .status(403)
          .json({ error: "A same-origin JSON request is required." });
    }
    next();
  });
  const user = async (req: Request): Promise<User> => {
    const session = await auth.api.getSession({
      headers: fromNodeHeaders(req.headers),
    });
    if (!session) throw new HttpError(401, "Please sign in to continue.");
    const row = db
      .prepare("SELECT id,name,email,role FROM user WHERE id=?")
      .get(session.user.id) as unknown as User | undefined;
    if (!row || !["customer", "provider", "admin"].includes(row.role))
      throw new HttpError(403, "Access denied.");
    return row;
  };
  const staff = (u: User) => {
    if (u.role === "customer")
      throw new HttpError(403, "Staff access is required.");
  };
  const admin = (u: User) => {
    if (u.role !== "admin")
      throw new HttpError(403, "Admin access is required.");
  };
  const getRequest = (id: string, u: User) => {
    const r = db
      .prepare("SELECT * FROM requests WHERE id=?")
      .get(id) as unknown as ServiceRequest | undefined;
    if (!r || (u.role === "customer" && r.customerId !== u.id))
      throw new HttpError(404, "Request not found.");
    return r;
  };
  const service = (id: string) => {
    const s = db
      .prepare("SELECT * FROM services WHERE id=?")
      .get(id) as unknown as Service | undefined;
    if (!s) throw new HttpError(404, "Service not found.");
    return { ...s, active: !!s.active };
  };
  const catalogueHistory = (s: Service, u: User, action: string) =>
    db
      .prepare("INSERT INTO catalogue_activity VALUES (?,?,?,?,?,?,?)")
      .run(
        randomUUID(),
        s.id,
        s.name,
        u.id,
        u.name,
        action,
        new Date().toISOString(),
      );
  const history = (r: ServiceRequest, u: User, action: string) =>
    db
      .prepare("INSERT INTO activity VALUES (?,?,?,?,?,?)")
      .run(randomUUID(), r.id, u.id, u.name, action, new Date().toISOString());
  const operation = (
    req: Request,
    u: User,
    scope: string,
    payload: unknown,
    work: () => unknown,
  ) => {
    const token = req.get("Idempotency-Key");
    if (!token || !/^[A-Za-z0-9_-]{8,100}$/.test(token))
      throw new HttpError(400, "A valid operation key is required.");
    const body = JSON.stringify(payload);
    db.exec("BEGIN IMMEDIATE");
    try {
      const existing = db
        .prepare("SELECT * FROM operations WHERE actorId=? AND token=?")
        .get(u.id, token) as
        { scope: string; payload: string; response: string } | undefined;
      if (existing) {
        if (existing.scope !== scope || existing.payload !== body)
          throw new HttpError(
            409,
            "This operation key was already used with different content.",
          );
        db.exec("COMMIT");
        return JSON.parse(existing.response);
      }
      const result = work();
      db.prepare("INSERT INTO operations VALUES (?,?,?,?,?)").run(
        u.id,
        token,
        scope,
        body,
        JSON.stringify(result),
      );
      db.exec("COMMIT");
      return result;
    } catch (e) {
      db.exec("ROLLBACK");
      throw e;
    }
  };
  app.get("/api/me", async (req, res) => {
    try {
      res.json({ user: await user(req) });
    } catch (e) {
      if (e instanceof HttpError && e.code === 401) res.json({ user: null });
      else throw e;
    }
  });
  app.get("/api/services", async (req, res) => {
    let isAdmin = false;
    try {
      isAdmin = (await user(req)).role === "admin";
    } catch (e) {
      if (!(e instanceof HttpError && e.code === 401)) throw e;
    }
    const rows = db
      .prepare(
        isAdmin
          ? "SELECT * FROM services ORDER BY rowid"
          : "SELECT * FROM services WHERE active=1 ORDER BY rowid",
      )
      .all();
    res.json({ services: rows.map((s) => ({ ...s, active: !!s.active })) });
  });
  app.get("/api/requests", async (req, res) => {
    const u = await user(req);
    res.json({
      requests:
        u.role === "customer"
          ? db
              .prepare(
                "SELECT * FROM requests WHERE customerId=? ORDER BY createdAt DESC",
              )
              .all(u.id)
          : db.prepare("SELECT * FROM requests ORDER BY createdAt DESC").all(),
    });
  });
  app.get("/api/requests/:id", async (req, res) => {
    const u = await user(req);
    const r = getRequest(String(req.params.id), u);
    res.json({
      request: r,
      history: db
        .prepare(
          "SELECT id,requestId,actorName,action,createdAt FROM activity WHERE requestId=? ORDER BY createdAt,rowid",
        )
        .all(r.id),
    });
  });
  app.post("/api/requests", async (req, res) => {
    const u = await user(req);
    if (u.role !== "customer")
      throw new HttpError(403, "Customer access is required.");
    const data = requestSchema.parse(req.body);
    res.status(201).json(
      operation(req, u, "create-request", data, () => {
        const s = service(data.serviceId);
        if (!s.active)
          throw new HttpError(409, "This service is currently unavailable.");
        const now = new Date().toISOString();
        const r: ServiceRequest = {
          ...data,
          preferredEndDate: data.preferredEndDate || null,
          id: randomUUID(),
          customerId: u.id,
          serviceName: s.name,
          servicePrice: s.price,
          status: "New",
          version: 1,
          createdAt: now,
          updatedAt: now,
        };
        const keys = Object.keys(r);
        db.prepare(
          `INSERT INTO requests (${keys.join(",")}) VALUES (${keys.map(() => "?").join(",")})`,
        ).run(...Object.values(r));
        history(r, u, "Request submitted");
        return { request: r };
      }),
    );
  });
  app.patch("/api/requests/:id/status", async (req, res) => {
    const u = await user(req);
    staff(u);
    const data = transitionSchema.parse(req.body);
    const id = String(req.params.id);
    res.json(
      operation(req, u, `status:${id}`, data, () => {
        const r = getRequest(id, u);
        if (r.version !== data.version)
          throw new HttpError(
            409,
            "This request changed. Refresh before trying again.",
          );
        const next: Record<string, string[]> = {
          New: ["Reviewing", "Declined"],
          Reviewing: ["Quoted", "Declined"],
          Quoted: ["Booked", "Declined"],
          Booked: ["Completed"],
          Completed: [],
          Declined: [],
        };
        if (!next[r.status]!.includes(data.status))
          throw new HttpError(409, "That status change is not allowed.");
        db.prepare(
          "UPDATE requests SET status=?,version=version+1,updatedAt=? WHERE id=?",
        ).run(data.status, new Date().toISOString(), id);
        const updated = getRequest(id, u);
        history(
          updated,
          u,
          `Status changed from ${r.status} to ${data.status}`,
        );
        return { request: updated };
      }),
    );
  });
  app.post("/api/requests/:id/draft", async (req, res) => {
    const u = await user(req);
    staff(u);
    const r = getRequest(String(req.params.id), u);
    try {
      res.json(await makeDraft(r, config));
    } catch {
      throw new HttpError(
        502,
        "Draft generation is unavailable. Please try again later.",
      );
    }
  });
  app.post("/api/services", async (req, res) => {
    const u = await user(req);
    admin(u);
    const data = serviceSchema.parse(req.body);
    res.status(201).json(
      operation(req, u, "create-service", data, () => {
        const id = randomUUID();
        db.prepare("INSERT INTO services VALUES (?,?,?,?,?,1)").run(
          id,
          data.name,
          data.description,
          data.price,
          Number(data.active),
        );
        const created = service(id);
        catalogueHistory(created, u, "Service created");
        return { service: created };
      }),
    );
  });
  app.patch("/api/services/:id", async (req, res) => {
    const u = await user(req);
    admin(u);
    const data = serviceSchema
      .extend({ version: z.number().int().positive() })
      .parse(req.body);
    const id = String(req.params.id);
    res.json(
      operation(req, u, `service:${id}`, data, () => {
        if (service(id).version !== data.version)
          throw new HttpError(
            409,
            "This service changed. Refresh before trying again.",
          );
        db.prepare(
          "UPDATE services SET name=?,description=?,price=?,active=?,version=version+1 WHERE id=?",
        ).run(data.name, data.description, data.price, Number(data.active), id);
        const updated = service(id);
        catalogueHistory(
          updated,
          u,
          `Service updated (${updated.active ? "active" : "inactive"})`,
        );
        return { service: updated };
      }),
    );
  });
  app.delete("/api/services/:id", async (req, res) => {
    const u = await user(req);
    admin(u);
    const version = z.coerce
      .number()
      .int()
      .positive()
      .parse(req.query.version ?? req.body?.version);
    const id = String(req.params.id);
    res.json(
      operation(req, u, `delete-service:${id}`, { version }, () => {
        if (service(id).version !== version)
          throw new HttpError(
            409,
            "This service changed. Refresh before trying again.",
          );
        if (
          db
            .prepare("SELECT id FROM requests WHERE serviceId=? LIMIT 1")
            .get(id)
        )
          throw new HttpError(
            409,
            "This service has request history. Deactivate it instead.",
          );
        catalogueHistory(service(id), u, "Service deleted");
        db.prepare("DELETE FROM services WHERE id=?").run(id);
        return { success: true };
      }),
    );
  });
  app.use("/api", (_req, res) =>
    res.status(404).json({ error: "Endpoint not found." }),
  );
  app.use(
    (error: unknown, _req: Request, res: Response, _next: NextFunction) => {
      if (error instanceof z.ZodError) {
        const fields: Record<string, string> = {};
        for (const issue of error.issues)
          fields[String(issue.path[0] || "form")] = issue.message;
        return res
          .status(400)
          .json({ error: "Please check the highlighted fields.", fields });
      }
      if (error instanceof HttpError)
        return res.status(error.code).json({ error: error.message });
      if (error instanceof SyntaxError)
        return res.status(400).json({ error: "Invalid JSON request." });
      res
        .status(500)
        .json({ error: "Something went wrong. Please try again." });
    },
  );
  return { app, db, auth, close: () => db.close() };
}
