import { describe, it, expect, beforeAll, afterAll } from "vitest";
import supertest from "supertest";
import { randomUUID } from "node:crypto";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { getMigrations } from "better-auth/db/migration";
import { openDatabase, migrateApplication } from "../src/server/database";
import { createApp } from "../src/server/app";
import { seedDatabase, DEMO_PASSWORD, accounts } from "../scripts/seed-data";
import type { RequestDetail } from "../src/shared/contracts";
const origin = "http://127.0.0.1:3100",
  secret = "synthetic-isolated-test-secret-at-least-32-characters";
let db: ReturnType<typeof openDatabase>,
  app: ReturnType<typeof createApp>["app"];
const cookies: Record<string, string> = {};
let dir: string;
const day = () => {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + 12);
  return d.toISOString().slice(0, 10);
};
const valid = () => ({
  serviceId: "small-repairs",
  description: "Two loose cupboard hinges need repairing.",
  location: "BS3 1AB",
  preferredFrom: day(),
  preferredTo: "",
  contactName: "Alex Morgan",
  contactEmail: "alex@demo.local",
  contactPhone: "07700 900123",
});
const call = (
  role: string,
  method: "get" | "post" | "patch" | "delete",
  path: string,
  body?: object | string,
  key: string = randomUUID(),
) => {
  const r = supertest(app)
    [method]("/api" + path)
    .set("Origin", origin)
    .set("Content-Type", "application/json")
    .set("Idempotency-Key", key);
  if (role) r.set("Cookie", cookies[role]);
  return body === undefined ? r : r.send(body);
};
async function newRequest(): Promise<RequestDetail> {
  const r = await call("alex", "post", "/requests", valid());
  expect(r.status).toBe(201);
  return r.body;
}
beforeAll(async () => {
  dir = mkdtempSync(join(tmpdir(), "serviceflow-test-"));
  db = openDatabase(join(dir, "test.sqlite"));
  const { runMigrations } = await getMigrations({
    database: db,
    advanced: { database: { validateSchema: false } },
  });
  await runMigrations();
  migrateApplication(db);
  await seedDatabase(db);
  app = createApp({ db, origin, secret, test: true }).app;
  for (const u of accounts) {
    const result = await call("", "post", "/auth/sign-in/email", {
      email: u.email,
      password: DEMO_PASSWORD,
    });
    expect(result.status).toBe(200);
    const set = result.headers["set-cookie"] as unknown as string[];
    cookies[u.email.split("@")[0]] = set.map((s) => s.split(";")[0]).join("; ");
  }
});
afterAll(() => {
  db?.close();
  if (dir) rmSync(dir, { recursive: true, force: true });
});
describe("Authentication, ownership and roles", () => {
  it("uses persisted mature-library sessions, rejects bad login and disabled signup", async () => {
    expect((await call("alex", "get", "/me")).body.role).toBe("customer");
    expect((await call("provider", "get", "/me")).body.role).toBe("provider");
    expect(
      (
        await call("", "post", "/auth/sign-in/email", {
          email: "alex@demo.local",
          password: "wrong-password",
        })
      ).status,
    ).toBe(401);
    expect(
      (
        await call("", "post", "/auth/sign-up/email", {
          email: "test@demo.local",
          password: DEMO_PASSWORD,
          name: "Bad",
        })
      ).status,
    ).toBe(404);
  });
  it("blocks unauthenticated reads and every mutation class", async () => {
    for (const path of [
      "/requests",
      "/requests/nonexistent",
      "/admin/services",
      "/admin/activity",
    ])
      expect((await call("", "get", path)).status).toBe(401);
    for (const [method, path, body] of [
      ["post", "/requests", valid()],
      ["post", "/services", {}],
      ["patch", "/services/x", {}],
      ["delete", "/services/x", {}],
      ["patch", "/requests/x/status", {}],
      ["post", "/requests/x/draft", {}],
    ] as const)
      expect((await call("", method, path, body)).status).toBe(401);
  });
  it("isolates customers through list, detail and history; blocks customer staff actions", async () => {
    const r = await newRequest();
    const list = await call("jamie", "get", "/requests");
    expect(
      list.body.every((x: RequestDetail) => x.customerId === "demo-jamie"),
    ).toBe(true);
    expect(list.body.some((x: RequestDetail) => x.id === r.id)).toBe(false);
    expect((await call("jamie", "get", "/requests/" + r.id)).status).toBe(404);
    expect(
      (await call("alex", "get", "/requests/" + r.id)).body.history,
    ).toHaveLength(1);
    for (const who of ["alex", "jamie"]) {
      expect(
        (await call(who, "post", "/requests/" + r.id + "/draft", {})).status,
      ).toBe(403);
      expect(
        (
          await call(who, "patch", "/requests/" + r.id + "/status", {
            status: "Reviewing",
            version: 0,
          })
        ).status,
      ).toBe(403);
    }
    expect((await call("provider", "get", "/requests/" + r.id)).status).toBe(
      200,
    );
    expect((await call("admin", "get", "/requests/" + r.id)).status).toBe(200);
  });
  it("rejects cross-site, missing-origin and non-JSON actions including auth", async () => {
    for (const path of [
      "/requests",
      "/auth/sign-in/email",
      "/requests/x/draft",
    ]) {
      expect(
        (
          await supertest(app)
            .post("/api" + path)
            .set("Cookie", cookies.alex)
            .set("Origin", "https://evil.invalid")
            .send(valid())
        ).status,
      ).toBe(403);
      expect(
        (
          await supertest(app)
            .post("/api" + path)
            .set("Cookie", cookies.alex)
            .send(valid())
        ).status,
      ).toBe(403);
    }
    expect(
      (
        await supertest(app)
          .post("/api/requests")
          .set("Origin", origin)
          .set("Cookie", cookies.alex)
          .type("form")
          .send({ description: "bad" })
      ).status,
    ).toBe(415);
    expect(
      (
        await supertest(app)
          .post("/api/requests")
          .set("Origin", origin)
          .set("Sec-Fetch-Site", "cross-site")
          .send(valid())
      ).status,
    ).toBe(403);
  });
  it("rejects provider/admin submissions and forged request fields", async () => {
    for (const who of ["provider", "admin"])
      expect((await call(who, "post", "/requests", valid())).status).toBe(403);
    const r = await call("alex", "post", "/requests", {
      ...valid(),
      customerId: "demo-jamie",
      status: "Completed",
    });
    expect(r.body.customerId).toBe("demo-alex");
    expect(r.body.status).toBe("New");
  });
  it("returns safe validation and API errors", async () => {
    const r = await call("alex", "post", "/requests", {
      ...valid(),
      contactEmail: "bad",
      preferredFrom: "2030-02-30",
    });
    expect(r.status).toBe(422);
    expect(r.body.fields).toHaveProperty("contactEmail");
    expect(r.body.fields).toHaveProperty("preferredFrom");
    const json = await supertest(app)
      .post("/api/requests")
      .set("Origin", origin)
      .set("Content-Type", "application/json")
      .send("{invalid");
    expect(json.status).toBe(400);
    expect(JSON.stringify(json.body)).not.toMatch(/stack|sqlite|node_modules/);
    expect((await call("alex", "get", "/missing")).status).toBe(404);
  });
});
describe("Workflow, atomic history and durable retries", () => {
  it("supports the full forward workflow and rejects skips, reverse and terminal moves", async () => {
    const r = await newRequest();
    let version = 0;
    for (const status of ["Reviewing", "Quoted", "Booked", "Completed"]) {
      const result = await call(
        "provider",
        "patch",
        "/requests/" + r.id + "/status",
        { status, version },
      );
      expect(result.status).toBe(200);
      expect(result.body.version).toBe(++version);
    }
    let before = await call("alex", "get", "/requests/" + r.id);
    expect(before.body.history).toHaveLength(5);
    for (const status of [
      "New",
      "Reviewing",
      "Quoted",
      "Booked",
      "Declined",
      "Completed",
    ])
      expect(
        (
          await call("provider", "patch", "/requests/" + r.id + "/status", {
            status,
            version,
          })
        ).status,
      ).toBe(409);
    expect(
      (await call("alex", "get", "/requests/" + r.id)).body.history,
    ).toEqual(before.body.history);
    const fresh = await newRequest();
    expect(
      (
        await call("provider", "patch", "/requests/" + fresh.id + "/status", {
          status: "Booked",
          version: 0,
        })
      ).status,
    ).toBe(409);
    expect(
      (
        await call("provider", "patch", "/requests/" + fresh.id + "/status", {
          status: "Reviewing",
          version: 0,
        })
      ).status,
    ).toBe(200);
    expect(
      (
        await call("provider", "patch", "/requests/" + fresh.id + "/status", {
          status: "New",
          version: 1,
        })
      ).status,
    ).toBe(409);
    expect(
      (await call("provider", "get", "/requests/" + fresh.id)).body.history,
    ).toHaveLength(2);
  });
  it("declines only New/Reviewing/Quoted; Booked cannot decline", async () => {
    for (const source of ["New", "Reviewing", "Quoted", "Booked"]) {
      let r = await newRequest();
      for (const status of ["Reviewing", "Quoted", "Booked"].slice(
        0,
        ["New", "Reviewing", "Quoted", "Booked"].indexOf(source),
      )) {
        r = (
          await call("admin", "patch", "/requests/" + r.id + "/status", {
            status,
            version: r.version,
          })
        ).body;
      }
      const result = await call(
        "provider",
        "patch",
        "/requests/" + r.id + "/status",
        { status: "Declined", version: r.version },
      );
      expect(result.status).toBe(source === "Booked" ? 409 : 200);
      if (source !== "Booked") {
        expect(
          (
            await call("provider", "patch", "/requests/" + r.id + "/status", {
              status: "Reviewing",
              version: result.body.version,
            })
          ).status,
        ).toBe(409);
      }
    }
  });
  it("rejects stale conflicting writes without activity", async () => {
    const r = await newRequest();
    const [a, b] = await Promise.all([
      call("provider", "patch", "/requests/" + r.id + "/status", {
        status: "Reviewing",
        version: 0,
      }),
      call("admin", "patch", "/requests/" + r.id + "/status", {
        status: "Declined",
        version: 0,
      }),
    ]);
    expect([a.status, b.status].sort()).toEqual([200, 409]);
    const detail = await call("alex", "get", "/requests/" + r.id);
    expect(detail.body.history).toHaveLength(2);
    expect(detail.body.version).toBe(1);
  });
  it("deduplicates request and status retries and rejects changed payload keys", async () => {
    const key = randomUUID(),
      input = valid();
    const a = await call("alex", "post", "/requests", input, key),
      b = await call("alex", "post", "/requests", input, key);
    expect(a.body.id).toBe(b.body.id);
    expect(b.body.history).toHaveLength(1);
    expect(
      (
        await call(
          "alex",
          "post",
          "/requests",
          { ...input, description: "A different job description" },
          key,
        )
      ).status,
    ).toBe(409);
    const updateKey = randomUUID(),
      body = { status: "Reviewing", version: 0 };
    const x = await call(
        "provider",
        "patch",
        "/requests/" + a.body.id + "/status",
        body,
        updateKey,
      ),
      y = await call(
        "provider",
        "patch",
        "/requests/" + a.body.id + "/status",
        body,
        updateKey,
      );
    expect(x.body).toEqual(y.body);
    expect(
      (await call("provider", "get", "/requests/" + a.body.id)).body.history,
    ).toHaveLength(2);
    expect(
      (await call("alex", "post", "/requests", input, "short")).status,
    ).toBe(400);
  });
  it("rolls back the mutation if activity persistence fails", async () => {
    const r = await newRequest();
    db.exec(
      "CREATE TRIGGER reject_history BEFORE INSERT ON activity BEGIN SELECT RAISE(ABORT,'synthetic activity failure'); END;",
    );
    try {
      const result = await call(
        "provider",
        "patch",
        "/requests/" + r.id + "/status",
        { status: "Reviewing", version: 0 },
      );
      expect(result.status).toBe(500);
      expect(JSON.stringify(result.body)).not.toContain("synthetic");
      expect((await call("alex", "get", "/requests/" + r.id)).body.status).toBe(
        "New",
      );
      expect(
        (await call("alex", "get", "/requests/" + r.id)).body.history,
      ).toHaveLength(1);
    } finally {
      db.exec("DROP TRIGGER reject_history");
    }
  });
  it("preserves sessions, requests, history and retry receipts across database reopen", async () => {
    const key = randomUUID(),
      input = valid(),
      r = await call("alex", "post", "/requests", input, key);
    await call("provider", "patch", "/requests/" + r.body.id + "/status", {
      status: "Reviewing",
      version: 0,
    });
    db.close();
    db = openDatabase(join(dir, "test.sqlite"));
    app = createApp({ db, origin, secret, test: true }).app;
    expect((await call("alex", "get", "/me")).status).toBe(200);
    const detail = await call("alex", "get", "/requests/" + r.body.id);
    expect(detail.body.status).toBe("Reviewing");
    expect(detail.body.history).toHaveLength(2);
    const retry = await call("alex", "post", "/requests", input, key);
    expect(retry.body.id).toBe(r.body.id);
    expect(
      (await call("alex", "get", "/requests")).body.filter(
        (x: RequestDetail) => x.id === r.body.id,
      ),
    ).toHaveLength(1);
  });
});
describe("Catalogue administration and historic integrity", () => {
  const service = {
    name: "Demo extra care",
    description: "A useful synthetic extra home-care service.",
    price: "Request a quote",
    category: "repair",
    active: true,
  };
  it("restricts catalogue and activity writes and reads to admin", async () => {
    for (const who of ["alex", "jamie", "provider"]) {
      expect((await call(who, "get", "/admin/services")).status).toBe(403);
      expect((await call(who, "get", "/admin/activity")).status).toBe(403);
      for (const [method, path] of [
        ["post", "/services"],
        ["patch", "/services/small-repairs"],
        ["delete", "/services/small-repairs"],
      ] as const)
        expect((await call(who, method, path, service)).status).toBe(403);
    }
  });
  it("creates, updates, activates, deactivates and deletes unused services with actor history", async () => {
    const key = randomUUID(),
      a = await call("admin", "post", "/services", service, key);
    expect(a.status).toBe(201);
    expect(
      (await call("admin", "post", "/services", service, key)).body.id,
    ).toBe(a.body.id);
    let r = await call("admin", "patch", "/services/" + a.body.id, {
      ...service,
      active: false,
      version: 0,
    });
    expect(r.status).toBe(200);
    expect(
      (await call("", "get", "/services")).body.some(
        (s: { id: string }) => s.id === a.body.id,
      ),
    ).toBe(false);
    expect(
      (await call("admin", "get", "/admin/services")).body.find(
        (s: { id: string }) => s.id === a.body.id,
      ).active,
    ).toBe(false);
    expect(
      (
        await call("alex", "post", "/requests", {
          ...valid(),
          serviceId: a.body.id,
        })
      ).status,
    ).toBe(422);
    expect(
      (
        await call("admin", "patch", "/services/" + a.body.id, {
          ...service,
          version: 0,
        })
      ).status,
    ).toBe(409);
    r = await call("admin", "patch", "/services/" + a.body.id, {
      ...service,
      name: "Updated demo care",
      version: 1,
    });
    expect(r.body.active).toBe(true);
    expect(
      (await call("admin", "delete", "/services/" + a.body.id, { version: 2 }))
        .status,
    ).toBe(200);
    expect(
      (
        await call("alex", "post", "/requests", {
          ...valid(),
          serviceId: a.body.id,
        })
      ).status,
    ).toBe(422);
    const logs = (await call("admin", "get", "/admin/activity")).body;
    expect(
      logs.filter(
        (x: { action: string }) =>
          x.action.includes("demo care") ||
          x.action.includes("Demo extra care"),
      ),
    ).toHaveLength(4);
    expect(
      logs.every((x: { actorName: string }) => x.actorName === "Robin Ellis"),
    ).toBe(true);
  });
  it("preserves service snapshots and prevents deleting a referenced service", async () => {
    const s = (
      await call("admin", "post", "/services", {
        ...service,
        name: "Historical service",
      })
    ).body;
    const r = (
      await call("alex", "post", "/requests", { ...valid(), serviceId: s.id })
    ).body;
    expect(
      (
        await call("admin", "patch", "/services/" + s.id, {
          ...service,
          name: "Renamed historical service",
          price: "From £99",
          active: false,
          version: 0,
        })
      ).status,
    ).toBe(200);
    expect(
      (await call("admin", "delete", "/services/" + s.id, { version: 1 }))
        .status,
    ).toBe(409);
    const detail = (await call("alex", "get", "/requests/" + r.id)).body;
    expect(detail.serviceName).toBe("Historical service");
    expect(detail.servicePrice).toBe("Request a quote");
    expect(
      (await call("alex", "post", "/requests", { ...valid(), serviceId: s.id }))
        .status,
    ).toBe(422);
    expect(detail.history).toHaveLength(1);
  });
});
describe("Staff-only unsent drafting", () => {
  it("allows provider/admin fallback drafts without status, activity, receipts or sent-message side effects", async () => {
    const r = await newRequest();
    const before = (await call("provider", "get", "/requests/" + r.id)).body;
    for (const who of ["provider", "admin"]) {
      const draft = await call(who, "post", "/requests/" + r.id + "/draft", {});
      expect(draft.status).toBe(200);
      expect(draft.body.source).toBe("deterministic");
      expect(draft.body.notice).toContain("Nothing has been sent");
    }
    expect((await call("alex", "get", "/requests/" + r.id)).body).toEqual(
      before,
    );
    expect(
      (await call("provider", "post", "/requests/not-found/draft", {})).status,
    ).toBe(404);
  });
});
