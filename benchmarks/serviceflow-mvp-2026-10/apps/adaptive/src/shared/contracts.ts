export const STATUSES = [
  "New",
  "Reviewing",
  "Quoted",
  "Booked",
  "Completed",
  "Declined",
] as const;
export type Status = (typeof STATUSES)[number];
export type Role = "customer" | "provider" | "admin";
export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}
export interface Service {
  id: string;
  name: string;
  description: string;
  price: string;
  active: boolean;
  version: number;
}
export interface ServiceRequest {
  id: string;
  customerId: string;
  serviceId: string;
  serviceName: string;
  servicePrice: string;
  description: string;
  location: string;
  preferredDate: string;
  preferredEndDate: string | null;
  contactName: string;
  contactEmail: string;
  contactPhone: string;
  status: Status;
  version: number;
  createdAt: string;
  updatedAt: string;
}
export interface Activity {
  id: string;
  requestId: string;
  actorName: string;
  action: string;
  createdAt: string;
}
export interface RequestDetail {
  request: ServiceRequest;
  history: Activity[];
}
export interface Draft {
  text: string;
  source: "deterministic-demo" | "configured-ai";
  reviewRequired: true;
}
export interface RequestInput {
  serviceId: string;
  description: string;
  location: string;
  preferredDate: string;
  preferredEndDate?: string;
  contactName: string;
  contactEmail: string;
  contactPhone: string;
}
export interface ApiErrorBody {
  error: string;
  fields?: Record<string, string>;
}
