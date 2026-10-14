import { describe, it, expect } from "vitest";
import { requestSchema, serviceSchema } from "../src/shared/contracts";
const future = () => {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + 10);
  return d.toISOString().slice(0, 10);
};
const valid = {
  serviceId: "small-repairs",
  description: "Fix the two loose kitchen shelves.",
  location: "BS3 1AB",
  preferredFrom: future(),
  preferredTo: "",
  contactName: "Alex Morgan",
  contactEmail: "Alex@demo.local",
  contactPhone: "07700 900123",
};
describe("Request validation", () => {
  it("trims inputs and normalizes email", () => {
    expect(
      requestSchema.parse({
        ...valid,
        contactName: " Alex Morgan ",
        description: " " + valid.description + " ",
      }),
    ).toMatchObject({
      contactName: "Alex Morgan",
      contactEmail: "alex@demo.local",
      description: valid.description,
    });
  });
  it.each([
    "description",
    "location",
    "contactName",
    "contactEmail",
    "contactPhone",
    "serviceId",
    "preferredFrom",
  ] as const)("rejects empty %s", (field) => {
    expect(requestSchema.safeParse({ ...valid, [field]: "" }).success).toBe(
      false,
    );
  });
  it("rejects past, impossible and reversed dates", () => {
    for (const v of [
      { preferredFrom: "2000-01-01" },
      { preferredFrom: "2030-02-30" },
      { preferredFrom: future(), preferredTo: "2020-01-01" },
    ])
      expect(requestSchema.safeParse({ ...valid, ...v }).success).toBe(false);
  });
  it("rejects oversized work and malformed contact details", () => {
    for (const v of [
      { description: "x".repeat(2001) },
      { contactEmail: "not-email" },
      { contactPhone: "-------" },
      { contactPhone: "call me maybe" },
    ])
      expect(requestSchema.safeParse({ ...valid, ...v }).success).toBe(false);
  });
  it("accepts optional date range and text without interpreting HTML", () => {
    expect(
      requestSchema.parse({
        ...valid,
        preferredTo: future(),
        description: '<script>alert("demo")</script>',
      }).description,
    ).toContain("<script>");
  });
  it("validates catalogue input and strips unauthorized properties", () => {
    expect(
      serviceSchema.safeParse({
        name: "A",
        description: "Short",
        price: "",
        active: true,
        category: "invalid",
      }).success,
    ).toBe(false);
    expect(
      requestSchema.parse({
        ...valid,
        customerId: "other",
        status: "Completed",
      }),
    ).not.toHaveProperty("status");
  });
});
