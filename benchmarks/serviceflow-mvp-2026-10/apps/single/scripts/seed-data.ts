import type Database from "better-sqlite3";
import { hashPassword } from "better-auth/crypto";
import { randomUUID } from "node:crypto";
import { Store } from "../src/server/domain.js";
import type { User, Status } from "../src/shared/contracts.js";
export const DEMO_PASSWORD = "ServiceFlow2026!";
export const accounts = [
  {
    id: "demo-alex",
    name: "Alex Morgan",
    email: "alex@demo.local",
    role: "customer",
  },
  {
    id: "demo-jamie",
    name: "Jamie Taylor",
    email: "jamie@demo.local",
    role: "customer",
  },
  {
    id: "demo-provider",
    name: "Sam Green",
    email: "provider@demo.local",
    role: "provider",
  },
  {
    id: "demo-admin",
    name: "Robin Ellis",
    email: "admin@demo.local",
    role: "admin",
  },
] as const;
export async function seedDatabase(db: Database.Database) {
  // Seed uses the library's own password hashing and account schema; existing accounts and state are preserved.
  const password = await hashPassword(DEMO_PASSWORD);
  db.transaction(() => {
    for (const u of accounts)
      if (!db.prepare("SELECT id FROM user WHERE email=?").get(u.email)) {
        const now = Date.now();
        db.prepare(
          "INSERT INTO user (id,name,email,emailVerified,createdAt,updatedAt) VALUES (?,?,?,1,?,?)",
        ).run(u.id, u.name, u.email, now, now);
        db.prepare(
          "INSERT INTO account (id,accountId,providerId,userId,password,createdAt,updatedAt) VALUES (?,?,?,?,?,?,?)",
        ).run(randomUUID(), u.id, "credential", u.id, password, now, now);
        db.prepare("INSERT INTO user_roles VALUES (?,?)").run(u.id, u.role);
      }
    const services = [
      [
        "small-repairs",
        "Small repairs",
        "From loose handles to shelves and everyday fixes. Tell us what needs a little attention.",
        "From £45",
        "repair",
      ],
      [
        "garden-care",
        "Garden care",
        "A tidy-up, lawn care or seasonal pruning to help your outdoor space feel its best.",
        "From £65",
        "garden",
      ],
      [
        "painting",
        "Painting & decorating",
        "Freshen a room with careful preparation, interior painting and finishing touches.",
        "Request a quote",
        "painting",
      ],
      [
        "home-cleaning",
        "Home cleaning",
        "A considered clean for kitchens, bathrooms and living spaces, tailored to your home.",
        "From £55",
        "cleaning",
      ],
    ];
    for (const s of services)
      db.prepare(
        "INSERT OR IGNORE INTO services (id,name,description,price,category,active) VALUES (?,?,?,?,?,1)",
      ).run(...s);
  })();
  const store = new Store(db),
    provider = accounts[2] as User;
  for (let i = 0; i < 6; i++) {
    const customer = accounts[i % 2] as User;
    const service = [
      "small-repairs",
      "garden-care",
      "painting",
      "home-cleaning",
    ][i % 4];
    const day = new Date();
    day.setUTCDate(day.getUTCDate() + 7 + i);
    const input = {
      serviceId: service,
      description: [
        "Two kitchen cupboard hinges are loose and a shelf needs fitting.",
        "A seasonal garden tidy, including lawn edging and a small hedge.",
        "Refresh the living room walls; approximately 20 square metres.",
        "A thorough clean of the kitchen and two bathrooms.",
      ][i % 4],
      location: ["BS3 1AB · South Bristol", "BS6 5CD · North Bristol"][i % 2],
      preferredFrom: day.toISOString().slice(0, 10),
      preferredTo: "",
      contactName: customer.name,
      contactEmail: customer.email,
      contactPhone: "07700 900" + (100 + i),
    };
    const key = "seed-request-0000" + i;
    if (
      db
        .prepare("SELECT key FROM mutation_receipts WHERE actorId=? AND key=?")
        .get(customer.id, key)
    )
      continue;
    const r = store.createRequest(customer, input, key);
    const target: Status = [
      "New",
      "Reviewing",
      "Quoted",
      "Booked",
      "Completed",
      "Declined",
    ][i] as Status;
    let current = r;
    for (const status of target === "Declined"
      ? (["Declined"] as Status[])
      : (["Reviewing", "Quoted", "Booked", "Completed"].slice(
          0,
          ["New", "Reviewing", "Quoted", "Booked", "Completed"].indexOf(target),
        ) as Status[]))
      current = store.changeStatus(
        provider,
        r.id,
        { status, version: current.version },
        `seed-status-000${i}-${status}`,
      );
  }
}
