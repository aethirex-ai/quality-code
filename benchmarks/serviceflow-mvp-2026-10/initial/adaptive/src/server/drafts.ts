import { z } from "zod";
import type { ServiceRequest, Draft } from "../shared/contracts.js";
import type { Config } from "./database.js";
// The provider receives only the work description, service and date preference.
export function minimizedPayload(request: ServiceRequest) {
  const personalNames = [request.contactName].filter((v) => v.length >= 3);
  let redacted = request.description;
  for (const name of personalNames)
    redacted = redacted.split(name).join("[name removed]");
  const description = redacted
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[email removed]")
    .replace(/(?:\+?\d[\d\s().-]{7,}\d)/g, "[phone removed]")
    .replace(/\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b/gi, "[postcode removed]");
  return {
    service: request.serviceName,
    description,
    preferredDate: request.preferredDate,
    preferredEndDate: request.preferredEndDate,
  };
}
const resultSchema = z.object({
  reply: z.string().trim().min(1).max(1800),
  questions: z.array(z.string().trim().min(1).max(250)).max(3),
});
export async function makeDraft(
  request: ServiceRequest,
  config: Config,
): Promise<Draft> {
  if (!config.aiKey)
    return {
      source: "deterministic-demo",
      reviewRequired: true,
      text: `Thank you for your ${request.serviceName.toLowerCase()} enquiry. We have received your description and your preferred date of ${request.preferredDate}${request.preferredEndDate ? ` to ${request.preferredEndDate}` : ""}. We will review the work before confirming availability or a quote.\n\nCould you share any useful measurements or details about the work? Are there any access considerations we should know about?\n\nNo appointment is confirmed at this stage.`,
    };
  if (!config.aiURL || !config.aiModel)
    throw new Error("Draft provider unavailable");
  const response = await (config.aiFetch || fetch)(config.aiURL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${config.aiKey}`,
    },
    signal: AbortSignal.timeout(12000),
    body: JSON.stringify({
      model: config.aiModel,
      messages: [
        {
          role: "system",
          content:
            "Draft a short customer-facing reply for fictional home service enquiries. Do not claim contact, a confirmed appointment or a confirmed price. Return JSON with reply and questions (at most three useful questions). No markdown.",
        },
        { role: "user", content: JSON.stringify(minimizedPayload(request)) },
      ],
      response_format: { type: "json_object" },
    }),
  });
  if (!response.ok) throw new Error("Draft provider unavailable");
  const envelope = (await response.json()) as {
    choices?: { message?: { content?: string } }[];
  };
  const value = resultSchema.parse(
    JSON.parse(envelope.choices?.[0]?.message?.content || ""),
  );
  // Questions must be explicit structured entries so the adapter can enforce the cap.
  if (
    (value.reply.match(/\?/g) || []).length ||
    value.questions.some((q) => (q.match(/\?/g) || []).length > 1)
  )
    throw new Error("Invalid draft provider response");
  return {
    source: "configured-ai",
    reviewRequired: true,
    text: [
      value.reply,
      ...value.questions.map((q) => (q.endsWith("?") ? q : q + "?")),
    ].join("\n\n"),
  };
}
