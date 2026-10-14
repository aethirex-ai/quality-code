import type Database from "better-sqlite3";
import { randomUUID, createHash } from "node:crypto";
import {
  requestSchema,
  serviceSchema,
  serviceUpdateSchema,
  statusSchema,
  transitions,
  versionSchema,
  type Service,
  type ServiceRequest,
  type User,
  type RequestDetail,
} from "../shared/contracts.js";
export class ProductError extends Error {
  constructor(
    public status: number,
    message: string,
    public fields?: Record<string, string>,
  ) {
    super(message);
  }
}
export function parse<T>(
  schema: {
    safeParse: (input: unknown) => {
      success: boolean;
      data?: T;
      error?: { issues: { path: PropertyKey[]; message: string }[] };
    };
  },
  input: unknown,
): T {
  const r = schema.safeParse(input);
  if (!r.success)
    throw new ProductError(
      422,
      "Please check the highlighted fields.",
      Object.fromEntries(
        r.error!.issues.map((i) => [i.path.join("."), i.message]),
      ),
    );
  return r.data!;
}
export class Store {
  constructor(public db: Database.Database) {}
  staff(user: User) {
    if (user.role === "customer")
      throw new ProductError(403, "Staff access is required.");
  }
  admin(user: User) {
    if (user.role !== "admin")
      throw new ProductError(403, "Only an administrator can manage services.");
  }
  services(user?: User): Service[] {
    return (
      this.db
        .prepare(
          `SELECT * FROM services ${user?.role === "admin" ? "" : "WHERE active=1"} ORDER BY rowid`,
        )
        .all() as Service[]
    ).map((s) => ({ ...s, active: !!s.active }));
  }
  requests(user: User): ServiceRequest[] {
    return this.db
      .prepare(
        `SELECT * FROM requests ${user.role === "customer" ? "WHERE customerId=?" : ""} ORDER BY createdAt DESC,id DESC`,
      )
      .all(...(user.role === "customer" ? [user.id] : [])) as ServiceRequest[];
  }
  detail(user: User, id: string): RequestDetail {
    const r = this.db.prepare("SELECT * FROM requests WHERE id=?").get(id) as
      ServiceRequest | undefined;
    if (!r || (user.role === "customer" && r.customerId !== user.id))
      throw new ProductError(404, "Request not found.");
    const history = this.db
      .prepare(
        "SELECT id,requestId,actorName,action,createdAt FROM activity WHERE requestId=? ORDER BY id",
      )
      .all(id) as RequestDetail["history"];
    return { ...r, history };
  }
  record(
    user: User,
    action: string,
    requestId: string | null = null,
    serviceId: string | null = null,
  ) {
    this.db
      .prepare(
        "INSERT INTO activity (requestId,serviceId,actorId,actorName,action,createdAt) VALUES (?,?,?,?,?,?)",
      )
      .run(
        requestId,
        serviceId,
        user.id,
        user.name,
        action,
        new Date().toISOString(),
      );
  }
  mutation<T>(
    user: User,
    key: unknown,
    operation: string,
    input: unknown,
    fn: () => T,
  ): T {
    if (typeof key !== "string" || !/^[A-Za-z0-9-]{16,80}$/.test(key))
      throw new ProductError(400, "A valid retry key is required.");
    const fingerprint = createHash("sha256")
      .update(JSON.stringify({ operation, input }))
      .digest("hex");
    return this.db
      .transaction(() => {
        const previous = this.db
          .prepare(
            "SELECT fingerprint,result FROM mutation_receipts WHERE actorId=? AND key=?",
          )
          .get(user.id, key) as
          { fingerprint: string; result: string } | undefined;
        if (previous) {
          if (previous.fingerprint !== fingerprint)
            throw new ProductError(
              409,
              "This retry key was already used for another action.",
            );
          return JSON.parse(previous.result) as T;
        }
        const result = fn();
        this.db
          .prepare("INSERT INTO mutation_receipts VALUES (?,?,?,?,?)")
          .run(
            user.id,
            key,
            fingerprint,
            JSON.stringify(result),
            new Date().toISOString(),
          );
        return result;
      })
      .immediate();
  }
  createRequest(user: User, input: unknown, key: unknown) {
    if (user.role !== "customer")
      throw new ProductError(
        403,
        "Only customers can submit service requests.",
      );
    const v = parse(requestSchema, input);
    return this.mutation(user, key, "request:create", v, () => {
      const service = this.db
        .prepare("SELECT * FROM services WHERE id=? AND active=1")
        .get(v.serviceId) as Service | undefined;
      if (!service)
        throw new ProductError(422, "This service is no longer available.", {
          serviceId: "Choose an active service.",
        });
      const id = randomUUID(),
        now = new Date().toISOString();
      this.db
        .prepare(
          `INSERT INTO requests (id,customerId,serviceId,serviceName,serviceDescription,servicePrice,description,location,preferredFrom,preferredTo,contactName,contactEmail,contactPhone,status,createdAt,updatedAt) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'New',?,?)`,
        )
        .run(
          id,
          user.id,
          service.id,
          service.name,
          service.description,
          service.price,
          v.description,
          v.location,
          v.preferredFrom,
          v.preferredTo,
          v.contactName,
          v.contactEmail,
          v.contactPhone,
          now,
          now,
        );
      this.record(user, "Request submitted", id);
      return this.detail(user, id);
    });
  }
  changeStatus(user: User, id: string, input: unknown, key: unknown) {
    this.staff(user);
    const v = parse(statusSchema, input);
    return this.mutation(user, key, "request:status:" + id, v, () => {
      const r = this.detail(user, id);
      if (r.version !== v.version)
        throw new ProductError(
          409,
          "This request changed. Reload its latest status before trying again.",
        );
      if (!transitions[r.status].includes(v.status))
        throw new ProductError(
          409,
          `Cannot move from ${r.status} to ${v.status}.`,
        );
      const result = this.db
        .prepare(
          "UPDATE requests SET status=?,version=version+1,updatedAt=? WHERE id=? AND version=?",
        )
        .run(v.status, new Date().toISOString(), id, v.version);
      if (result.changes !== 1)
        throw new ProductError(
          409,
          "This request changed. Reload and try again.",
        );
      this.record(user, `Status changed: ${r.status} → ${v.status}`, id);
      return this.detail(user, id);
    });
  }
  createService(user: User, input: unknown, key: unknown) {
    this.admin(user);
    const v = parse(serviceSchema, input);
    return this.mutation(user, key, "service:create", v, () => {
      const id = randomUUID();
      this.db
        .prepare(
          "INSERT INTO services (id,name,description,price,category,active) VALUES (?,?,?,?,?,?)",
        )
        .run(id, v.name, v.description, v.price, v.category, Number(v.active));
      this.record(user, `Service created: ${v.name}`, null, id);
      return this.services(user).find((s) => s.id === id)!;
    });
  }
  updateService(user: User, id: string, input: unknown, key: unknown) {
    this.admin(user);
    const v = parse(serviceUpdateSchema, input);
    return this.mutation(user, key, "service:update:" + id, v, () => {
      const s = this.db.prepare("SELECT * FROM services WHERE id=?").get(id) as
        Service | undefined;
      if (!s) throw new ProductError(404, "Service not found.");
      if (s.version !== v.version)
        throw new ProductError(
          409,
          "This service changed. Reload before saving.",
        );
      this.db
        .prepare(
          "UPDATE services SET name=?,description=?,price=?,category=?,active=?,version=version+1 WHERE id=? AND version=?",
        )
        .run(
          v.name,
          v.description,
          v.price,
          v.category,
          Number(v.active),
          id,
          v.version,
        );
      this.record(
        user,
        `Service updated: ${v.name}${!!s.active !== v.active ? (v.active ? " · activated" : " · deactivated") : ""}`,
        null,
        id,
      );
      return this.services(user).find((s) => s.id === id)!;
    });
  }
  deleteService(user: User, id: string, input: unknown, key: unknown) {
    this.admin(user);
    const v = parse(versionSchema, input);
    return this.mutation(user, key, "service:delete:" + id, v, () => {
      const s = this.db.prepare("SELECT * FROM services WHERE id=?").get(id) as
        Service | undefined;
      if (!s) throw new ProductError(404, "Service not found.");
      if (s.version !== v.version)
        throw new ProductError(
          409,
          "This service changed. Reload before deleting.",
        );
      if (
        this.db
          .prepare("SELECT id FROM requests WHERE serviceId=? LIMIT 1")
          .get(id)
      )
        throw new ProductError(
          409,
          "This service has request history. Deactivate it instead.",
        );
      this.record(user, `Service deleted: ${s.name}`, null, id);
      this.db.prepare("DELETE FROM services WHERE id=?").run(id);
      return { deleted: true };
    });
  }
}
