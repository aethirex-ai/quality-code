import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { Server } from "node:http";
import { createApp } from "../src/server/app.js";
import { seedDatabase, type Config } from "../src/server/database.js";
import { minimizedPayload, makeDraft } from "../src/server/drafts.js";
import type { ServiceRequest } from "../src/shared/contracts.js";

const origin = "http://127.0.0.1:3000";
const valid = {
  serviceId: "plumbing-repairs",
  description: "The kitchen tap drips steadily after closing it.",
  location: "BS1 4QA, Bristol",
  preferredDate: "2099-04-10",
  contactName: "Jamie Morgan",
  contactEmail: "jamie@example.test",
  contactPhone: "07700 900123",
};
async function fixture(extra: Partial<Config> = {}) {
  const dir = mkdtempSync(join(tmpdir(), "serviceflow-test-"));
  const config: Config = {
    databasePath: join(dir, "test.sqlite"),
    baseURL: origin,
    secret: "a-secure-synthetic-test-secret-of-more-than-32-characters",
    ...extra,
  };
  let runtime = await createApp(config);
  await seedDatabase(runtime.db, config, false);
  let server: Server = runtime.app.listen(0, "127.0.0.1");
  await new Promise<void>((r) => server.once("listening", r));
  let base = `http://127.0.0.1:${(server.address() as { port: number }).port}`;
  async function call(
    path: string,
    method = "GET",
    body?: unknown,
    cookie = "",
    key?: string,
    requestOrigin = origin,
  ) {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Origin: requestOrigin,
    };
    if (cookie) headers.Cookie = cookie;
    if (key) headers["Idempotency-Key"] = key;
    const response = await fetch(base + path, {
      method,
      headers,
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    const data = await response.json();
    return {
      status: response.status,
      data,
      cookie: response.headers
        .getSetCookie()
        .map((c) => c.split(";")[0])
        .join("; "),
    };
  }
  async function login(role: string) {
    const r = await call("/api/auth/sign-in/email", "POST", {
      email: `${role}@serviceflow.demo`,
      password: "DemoHome2026!",
    });
    assert.equal(r.status, 200, JSON.stringify(r.data));
    assert.ok(r.cookie);
    return r.cookie;
  }
  async function stop() {
    await new Promise<void>((r, j) => server.close((e) => (e ? j(e) : r())));
    runtime.close();
  }
  return {
    config,
    call,
    login,
    get db() {
      return runtime.db;
    },
    async restart() {
      await stop();
      runtime = await createApp(config);
      server = runtime.app.listen(0, "127.0.0.1");
      await new Promise<void>((r) => server.once("listening", r));
      base = `http://127.0.0.1:${(server.address() as { port: number }).port}`;
    },
    async close() {
      await stop();
      rmSync(dir, { recursive: true, force: true });
    },
  };
}

test("real auth: disabled signup, database roles, unauthenticated and cross-origin writes", async () => {
  const f = await fixture();
  try {
    assert.equal((await f.call("/api/me")).data.user, null);
    assert.equal((await f.call("/api/requests")).status, 401);
    assert.equal(
      (
        await f.call("/api/auth/sign-up/email", "POST", {
          email: "attack@example.test",
          password: "SyntheticPassword123!",
          name: "Attacker",
          role: "admin",
        })
      ).status,
      400,
    );
    const customer = await f.login("customer");
    assert.equal(
      (await f.call("/api/me", "GET", undefined, customer)).data.user.role,
      "customer",
    );
    assert.equal(
      (
        await f.call(
          "/api/auth/update-user",
          "POST",
          { role: "admin" },
          customer,
        )
      ).status,
      400,
    );
    assert.equal(
      (await f.call("/api/me", "GET", undefined, customer)).data.user.role,
      "customer",
    );
    assert.equal(
      (
        await f.call(
          "/api/requests",
          "POST",
          valid,
          customer,
          "origin-key-001",
          "https://evil.test",
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await f.call(
          "/api/auth/sign-in/email",
          "POST",
          { email: "customer@serviceflow.demo", password: "DemoHome2026!" },
          "",
          "auth-origin-01",
          "https://evil.test",
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await f.call(
          "/api/requests",
          "POST",
          valid,
          customer,
          "origin-key-002",
          "",
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await f.call("/api/auth/sign-in/email", "POST", {
          email: "customer@serviceflow.demo",
          password: "wrong-password",
        })
      ).status,
      401,
    );
    assert.equal(
      f.db.prepare("SELECT COUNT(*) AS n FROM requests").get()!.n,
      0,
    );
  } finally {
    await f.close();
  }
});

test("customer submission validates and normalizes, owns reads, retries exactly once, survives restart", async () => {
  const f = await fixture();
  try {
    const c1 = await f.login("customer"),
      c2 = await f.login("customer2"),
      provider = await f.login("provider");
    const bad = await f.call(
      "/api/requests",
      "POST",
      { ...valid, preferredDate: "2099-02-31" },
      c1,
      "request-bad-001",
    );
    assert.equal(bad.status, 400);
    assert.ok(bad.data.fields.preferredDate);
    assert.equal(
      (
        await f.call(
          "/api/requests",
          "POST",
          { ...valid, preferredEndDate: "2099-04-09" },
          c1,
          "request-bad-002",
        )
      ).status,
      400,
    );
    assert.equal(
      (
        await f.call(
          "/api/requests",
          "POST",
          { ...valid, preferredDate: "2020-01-01" },
          c1,
          "request-bad-003",
        )
      ).status,
      400,
    );
    assert.equal(
      (
        await f.call(
          "/api/requests",
          "POST",
          { ...valid, role: "admin" },
          c1,
          "request-bad-004",
        )
      ).status,
      400,
    );
    assert.equal(
      (
        await f.call(
          "/api/requests",
          "POST",
          { ...valid, contactPhone: "-------" },
          c1,
          "request-bad-006",
        )
      ).status,
      400,
    );
    assert.equal(
      (
        await f.call(
          "/api/requests",
          "POST",
          valid,
          provider,
          "request-bad-005",
        )
      ).status,
      403,
    );
    assert.equal(
      (await f.call("/api/requests", "POST", valid, c1)).status,
      400,
    );
    const payload = {
      ...valid,
      description: "  " + valid.description + "  ",
      contactEmail: " JAMIE@EXAMPLE.TEST ",
    };
    const first = await f.call(
      "/api/requests",
      "POST",
      payload,
      c1,
      "request-good-001",
    );
    assert.equal(first.status, 201);
    const id = first.data.request.id;
    assert.equal(first.data.request.description, valid.description);
    assert.equal(first.data.request.contactEmail, "jamie@example.test");
    assert.deepEqual(
      (await f.call("/api/requests", "POST", payload, c1, "request-good-001"))
        .data,
      first.data,
    );
    assert.equal(
      (
        await f.call(
          "/api/requests",
          "POST",
          { ...payload, description: "Different request description" },
          c1,
          "request-good-001",
        )
      ).status,
      409,
    );
    assert.equal(
      (await f.call("/api/requests", "GET", undefined, c1)).data.requests
        .length,
      1,
    );
    assert.equal(
      (await f.call("/api/requests", "GET", undefined, c2)).data.requests
        .length,
      0,
    );
    assert.equal(
      (await f.call("/api/requests/" + id, "GET", undefined, c2)).status,
      404,
    );
    assert.equal(
      (await f.call("/api/requests/" + id + "/draft", "POST", {}, c1)).status,
      403,
    );
    assert.equal(
      (
        await f.call(
          "/api/requests/" + id + "/status",
          "PATCH",
          { status: "Reviewing", version: 1 },
          c1,
          "customer-status-1",
        )
      ).status,
      403,
    );
    assert.equal(
      (await f.call("/api/requests/" + id, "GET", undefined, provider)).data
        .history.length,
      1,
    );
    await f.restart();
    assert.equal(
      (await f.call("/api/requests/" + id, "GET", undefined, c1)).data.request
        .id,
      id,
    );
    assert.deepEqual(
      (await f.call("/api/requests", "POST", payload, c1, "request-good-001"))
        .data,
      first.data,
    );
  } finally {
    await f.close();
  }
});

test("workflow rejects skips, stale versions, backwards and terminal moves; history is transactional", async () => {
  const f = await fixture();
  try {
    const customer = await f.login("customer"),
      provider = await f.login("provider"),
      admin = await f.login("admin");
    const created = await f.call(
      "/api/requests",
      "POST",
      valid,
      customer,
      "workflow-create-1",
    );
    const id = created.data.request.id;
    const path = "/api/requests/" + id;
    assert.equal(
      (
        await f.call(
          path + "/status",
          "PATCH",
          { status: "Booked", version: 1 },
          provider,
          "workflow-skip-1",
        )
      ).status,
      409,
    );
    const reviewed = await f.call(
      path + "/status",
      "PATCH",
      { status: "Reviewing", version: 1 },
      provider,
      "workflow-review-1",
    );
    assert.equal(reviewed.status, 200);
    assert.equal(reviewed.data.request.version, 2);
    assert.deepEqual(
      (
        await f.call(
          path + "/status",
          "PATCH",
          { status: "Reviewing", version: 1 },
          provider,
          "workflow-review-1",
        )
      ).data,
      reviewed.data,
    );
    assert.equal(
      (
        await f.call(
          path + "/status",
          "PATCH",
          { status: "Quoted", version: 1 },
          admin,
          "workflow-stale-1",
        )
      ).status,
      409,
    );
    assert.equal(
      (
        await f.call(
          path + "/status",
          "PATCH",
          { status: "New", version: 2 },
          provider,
          "workflow-back-1",
        )
      ).status,
      409,
    );
    assert.equal(
      (
        await f.call(
          path + "/status",
          "PATCH",
          { status: "Quoted", version: 2 },
          provider,
          "workflow-review-1",
        )
      ).status,
      409,
    );
    for (const [status, version] of [
      ["Quoted", 2],
      ["Booked", 3],
      ["Completed", 4],
    ] as const)
      assert.equal(
        (
          await f.call(
            path + "/status",
            "PATCH",
            { status, version },
            provider,
            `workflow-${status}`,
          )
        ).status,
        200,
      );
    assert.equal(
      (
        await f.call(
          path + "/status",
          "PATCH",
          { status: "Declined", version: 5 },
          provider,
          "workflow-terminal-1",
        )
      ).status,
      409,
    );
    const detail = (await f.call(path, "GET", undefined, customer)).data;
    assert.equal(detail.history.length, 5);
    assert.equal(detail.request.status, "Completed");
    assert.ok(
      detail.history.every(
        (a: { actorName: string; createdAt: string }) =>
          a.actorName && a.createdAt,
      ),
    );
    const other = (
      await f.call(
        "/api/requests",
        "POST",
        valid,
        customer,
        "workflow-create-2",
      )
    ).data.request.id;
    assert.equal(
      (
        await f.call(
          `/api/requests/${other}/status`,
          "PATCH",
          { status: "Declined", version: 1 },
          admin,
          "workflow-decline",
        )
      ).status,
      200,
    );
    assert.equal(
      (
        await f.call(
          `/api/requests/${other}/status`,
          "PATCH",
          { status: "Reviewing", version: 2 },
          admin,
          "workflow-terminal-2",
        )
      ).status,
      409,
    );
    const third = (
      await f.call(
        "/api/requests",
        "POST",
        valid,
        customer,
        "workflow-create-3",
      )
    ).data.request.id;
    for (const [status, version] of [
      ["Reviewing", 1],
      ["Quoted", 2],
      ["Booked", 3],
    ] as const)
      await f.call(
        `/api/requests/${third}/status`,
        "PATCH",
        { status, version },
        provider,
        `third-${status}`,
      );
    assert.equal(
      (
        await f.call(
          `/api/requests/${third}/status`,
          "PATCH",
          { status: "Declined", version: 4 },
          provider,
          "workflow-book-decline",
        )
      ).status,
      409,
    );
  } finally {
    await f.close();
  }
});

test("admin catalogue CRUD optimistic locking, idempotency, inactive availability and historical preservation", async () => {
  const f = await fixture();
  try {
    const admin = await f.login("admin"),
      provider = await f.login("provider"),
      customer = await f.login("customer");
    const input = {
      name: "Window repairs",
      description: "Repair sticky windows and broken handles.",
      price: "From £70",
      active: true,
    };
    assert.equal(
      (
        await f.call(
          "/api/services",
          "POST",
          input,
          provider,
          "service-denied-1",
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await f.call(
          "/api/services",
          "POST",
          input,
          customer,
          "service-denied-2",
        )
      ).status,
      403,
    );
    const add = await f.call(
      "/api/services",
      "POST",
      input,
      admin,
      "service-create-1",
    );
    assert.equal(add.status, 201);
    const id = add.data.service.id;
    assert.deepEqual(
      (await f.call("/api/services", "POST", input, admin, "service-create-1"))
        .data,
      add.data,
    );
    assert.equal(
      (
        await f.call(
          "/api/services",
          "POST",
          { ...input, price: "From £80" },
          admin,
          "service-create-1",
        )
      ).status,
      409,
    );
    const req = (
      await f.call(
        "/api/requests",
        "POST",
        { ...valid, serviceId: id },
        customer,
        "service-request-1",
      )
    ).data.request;
    const patch = await f.call(
      "/api/services/" + id,
      "PATCH",
      {
        ...input,
        name: "Window maintenance",
        price: "From £85",
        active: false,
        version: 1,
      },
      admin,
      "service-patch-1",
    );
    assert.equal(patch.status, 200);
    assert.deepEqual(
      (
        await f.call(
          "/api/services/" + id,
          "PATCH",
          {
            ...input,
            name: "Window maintenance",
            price: "From £85",
            active: false,
            version: 1,
          },
          admin,
          "service-patch-1",
        )
      ).data,
      patch.data,
    );
    assert.equal(
      (
        await f.call(
          "/api/services/" + id,
          "PATCH",
          { ...input, version: 1 },
          admin,
          "service-patch-stale",
        )
      ).status,
      409,
    );
    assert.equal(
      (
        await f.call(
          "/api/requests",
          "POST",
          { ...valid, serviceId: id },
          customer,
          "service-inactive-1",
        )
      ).status,
      409,
    );
    assert.ok(
      !(await f.call("/api/services")).data.services.find(
        (s: { id: string }) => s.id === id,
      ),
    );
    assert.ok(
      (
        await f.call("/api/services", "GET", undefined, admin)
      ).data.services.find((s: { id: string }) => s.id === id),
    );
    const history = (
      await f.call("/api/requests/" + req.id, "GET", undefined, customer)
    ).data;
    assert.equal(history.request.serviceName, input.name);
    assert.equal(history.request.servicePrice, input.price);
    assert.equal(
      (
        await f.call(
          "/api/services/" + id + "?version=2",
          "DELETE",
          {},
          admin,
          "service-delete-ref",
        )
      ).status,
      409,
    );
    const disposable = (
      await f.call("/api/services", "POST", input, admin, "service-disposable")
    ).data.service.id;
    const deletion = await f.call(
      "/api/services/" + disposable + "?version=1",
      "DELETE",
      {},
      admin,
      "service-delete-1",
    );
    assert.equal(deletion.status, 200);
    assert.deepEqual(
      (
        await f.call(
          "/api/services/" + disposable + "?version=1",
          "DELETE",
          {},
          admin,
          "service-delete-1",
        )
      ).data,
      deletion.data,
    );
    const records = f.db
      .prepare("SELECT * FROM catalogue_activity WHERE serviceId=?")
      .all(disposable);
    assert.equal(records.length, 2);
    assert.ok(records.every((r) => r.actorName && r.createdAt));
    assert.equal(records[1]!.action, "Service deleted");
  } finally {
    await f.close();
  }
});

test("authorized deterministic drafts have no status/history effects; configured adapter is mocked and minimized", async () => {
  const f = await fixture();
  try {
    const customer = await f.login("customer"),
      provider = await f.login("provider");
    const request = (
      await f.call("/api/requests", "POST", valid, customer, "draft-create-1")
    ).data.request as ServiceRequest;
    const draft = await f.call(
      `/api/requests/${request.id}/draft`,
      "POST",
      {},
      provider,
    );
    assert.equal(draft.status, 200);
    assert.equal(draft.data.source, "deterministic-demo");
    assert.equal(draft.data.reviewRequired, true);
    assert.ok((draft.data.text.match(/\?/g) || []).length <= 3);
    const detail = (
      await f.call("/api/requests/" + request.id, "GET", undefined, provider)
    ).data;
    assert.equal(detail.request.version, 1);
    assert.equal(detail.history.length, 1);
    const privateRequest = {
      ...request,
      description:
        "Please repair tap. Reach me at jamie@example.test or 07700 900123, BS1 4QA.",
    };
    const safe = minimizedPayload(privateRequest);
    assert.ok(!JSON.stringify(safe).includes("jamie@"));
    assert.ok(!JSON.stringify(safe).includes("07700"));
    assert.ok(!JSON.stringify(safe).includes("BS1"));
    assert.ok(!("contactName" in safe));
    assert.ok(!("location" in safe));
    let calls = 0;
    const config = {
      ...f.config,
      aiKey: "synthetic-mock-key",
      aiURL: "https://mock.invalid/draft",
      aiModel: "mock-model",
      aiFetch: (async (_url, options) => {
        calls++;
        const body = JSON.parse(String(options?.body));
        assert.equal(body.model, "mock-model");
        assert.ok(!JSON.stringify(body).includes("jamie@"));
        return new Response(
          JSON.stringify({
            choices: [
              {
                message: {
                  content: JSON.stringify({
                    reply: "Thank you. We will review the requested repair.",
                    questions: ["What size is the tap?"],
                  }),
                },
              },
            ],
          }),
          { status: 200 },
        );
      }) as typeof fetch,
    };
    const configured = await makeDraft(privateRequest, config);
    assert.equal(calls, 1);
    assert.equal(configured.source, "configured-ai");
    assert.equal(configured.reviewRequired, true);
    await assert.rejects(() =>
      makeDraft(privateRequest, {
        ...config,
        aiFetch: (async () =>
          new Response(
            JSON.stringify({
              choices: [
                {
                  message: {
                    content: JSON.stringify({
                      reply: "Thanks.",
                      questions: ["One", "Two", "Three", "Four"],
                    }),
                  },
                },
              ],
            }),
          )) as typeof fetch,
      }),
    );
    await assert.rejects(() =>
      makeDraft(privateRequest, {
        ...config,
        aiFetch: (async () =>
          new Response("{}", { status: 503 })) as typeof fetch,
      }),
    );
  } finally {
    await f.close();
  }
});

test("configured draft HTTP adapter mocks success and safe provider errors without changing request state", async () => {
  let fail = false,
    calls = 0;
  const f = await fixture({
    aiKey: "synthetic-mock-secret",
    aiURL: "https://mock.invalid",
    aiModel: "mock",
    aiFetch: (async () => {
      calls++;
      if (fail)
        return new Response("upstream-secret-stacktrace", { status: 500 });
      return new Response(
        JSON.stringify({
          choices: [
            {
              message: {
                content: JSON.stringify({
                  reply: "Thank you. We will review these details.",
                  questions: ["Is there easy access to the tap?"],
                }),
              },
            },
          ],
        }),
      );
    }) as typeof fetch,
  });
  try {
    const customer = await f.login("customer"),
      provider = await f.login("provider");
    const request = (
      await f.call(
        "/api/requests",
        "POST",
        valid,
        customer,
        "configured-create",
      )
    ).data.request;
    assert.equal(
      (await f.call(`/api/requests/${request.id}/draft`, "POST", {}, customer))
        .status,
      403,
    );
    assert.equal(calls, 0);
    const draft = await f.call(
      `/api/requests/${request.id}/draft`,
      "POST",
      {},
      provider,
    );
    assert.equal(draft.status, 200);
    assert.equal(draft.data.source, "configured-ai");
    assert.equal(draft.data.reviewRequired, true);
    fail = true;
    const failed = await f.call(
      `/api/requests/${request.id}/draft`,
      "POST",
      {},
      provider,
    );
    assert.equal(failed.status, 502);
    assert.deepEqual(failed.data, {
      error: "Draft generation is unavailable. Please try again later.",
    });
    const detail = (
      await f.call("/api/requests/" + request.id, "GET", undefined, provider)
    ).data;
    assert.equal(detail.request.version, 1);
    assert.equal(detail.history.length, 1);
  } finally {
    await f.close();
  }
});

test("demo seed is idempotent with two owners and chronological valid workflow history", async () => {
  const f = await fixture();
  try {
    await seedDatabase(f.db, f.config, true);
    await seedDatabase(f.db, f.config, true);
    const rows = f.db.prepare("SELECT * FROM requests").all();
    assert.equal(rows.length, 8);
    assert.equal(new Set(rows.map((r) => r.customerId)).size, 2);
    assert.equal(f.db.prepare("SELECT COUNT(*) AS n FROM user").get()!.n, 4);
    assert.equal(
      f.db.prepare("SELECT COUNT(*) AS n FROM services").get()!.n,
      4,
    );
    for (const request of rows) {
      const history = f.db
        .prepare("SELECT * FROM activity WHERE requestId=? ORDER BY createdAt")
        .all(request.id!);
      assert.equal(history.length, request.version);
      assert.equal(history[0]!.action, "Request submitted");
      assert.ok(history.every((a) => a.actorId && a.actorName && a.createdAt));
    }
  } finally {
    await f.close();
  }
});
