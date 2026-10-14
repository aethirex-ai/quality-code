import { z } from "zod";
export const statuses = [
  "New",
  "Reviewing",
  "Quoted",
  "Booked",
  "Completed",
  "Declined",
] as const;
export type Status = (typeof statuses)[number];
export type Role = "customer" | "provider" | "admin";
export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}
export const transitions: Record<Status, Status[]> = {
  New: ["Reviewing", "Declined"],
  Reviewing: ["Quoted", "Declined"],
  Quoted: ["Booked", "Declined"],
  Booked: ["Completed"],
  Completed: [],
  Declined: [],
};
const text = (min: number, max: number) =>
  z
    .string()
    .trim()
    .min(min, `Use at least ${min} characters.`)
    .max(max, `Use no more than ${max} characters.`);
const date = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Choose a date.")
  .refine((v) => {
    const d = new Date(v + "T00:00:00Z");
    return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === v;
  }, "Choose a valid date.");
export const requestSchema = z
  .object({
    serviceId: z.string().trim().min(1, "Choose a service.").max(80),
    description: text(12, 2000),
    location: text(3, 160),
    preferredFrom: date,
    preferredTo: z
      .union([date, z.literal("")])
      .optional()
      .default(""),
    contactName: text(2, 100),
    contactEmail: z
      .string()
      .trim()
      .email("Enter a valid email.")
      .max(160)
      .transform((v) => v.toLowerCase()),
    contactPhone: text(7, 30)
      .regex(/^[+()\d\s.-]+$/, "Use a valid phone number.")
      .refine(
        (v) => v.replace(/\D/g, "").length >= 7,
        "Use at least seven digits.",
      ),
  })
  .superRefine((v, ctx) => {
    if (v.preferredFrom < new Date().toISOString().slice(0, 10))
      ctx.addIssue({
        code: "custom",
        path: ["preferredFrom"],
        message: "Choose today or a future date.",
      });
    if (v.preferredTo && v.preferredTo < v.preferredFrom)
      ctx.addIssue({
        code: "custom",
        path: ["preferredTo"],
        message: "End date must be on or after the start date.",
      });
  });
export const serviceSchema = z.object({
  name: text(3, 80),
  description: text(12, 600),
  price: text(3, 80),
  category: z.enum(["repair", "garden", "painting", "cleaning"]),
  active: z.boolean(),
});
export const statusSchema = z.object({
  status: z.enum(statuses),
  version: z.number().int().min(0),
});
export const serviceUpdateSchema = serviceSchema.extend({
  version: z.number().int().min(0),
});
export const versionSchema = z.object({ version: z.number().int().min(0) });
export interface Service {
  id: string;
  name: string;
  description: string;
  price: string;
  category: "repair" | "garden" | "painting" | "cleaning";
  active: boolean;
  version: number;
}
export interface ServiceRequest {
  id: string;
  customerId: string;
  serviceId: string;
  serviceName: string;
  serviceDescription: string;
  servicePrice: string;
  description: string;
  location: string;
  preferredFrom: string;
  preferredTo: string;
  contactName: string;
  contactEmail: string;
  contactPhone: string;
  status: Status;
  version: number;
  createdAt: string;
  updatedAt: string;
}
export interface Activity {
  id: number;
  requestId: string | null;
  actorName: string;
  action: string;
  createdAt: string;
}
export interface RequestDetail extends ServiceRequest {
  history: Activity[];
}
export interface Draft {
  text: string;
  source: "deterministic" | "ai";
  notice: string;
}
