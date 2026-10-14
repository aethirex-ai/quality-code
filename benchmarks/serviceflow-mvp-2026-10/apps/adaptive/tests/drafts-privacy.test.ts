import { test } from "node:test";
import assert from "node:assert/strict";
import { makeDraft } from "../src/server/drafts.js";
import type { ServiceRequest } from "../src/shared/contracts.js";

// Exercise the serialized configured-provider boundary, not just its helper.
// Fetch is always mocked; the test never requests credentials or uses the network.
const request: ServiceRequest = {
  id: "privacy-regression-request",
  customerId: "synthetic-customer",
  serviceId: "plumbing-repairs",
  serviceName: "Plumbing repairs",
  servicePrice: "From £65",
  description: "Please repair my tap. My name is jamie morgan.",
  location: "BS1 4QA, Bristol",
  preferredDate: "2099-04-10",
  preferredEndDate: null,
  contactName: "Jamie Morgan",
  contactEmail: "jamie@example.test",
  contactPhone: "07700 900123",
  status: "New",
  version: 1,
  createdAt: "2026-10-14T00:00:00.000Z",
  updatedAt: "2026-10-14T00:00:00.000Z",
};

async function assertPrivateProviderPayload(
  contactName: string,
  variants: string[],
) {
  let calls = 0;
  const result = await makeDraft(
    {
      ...request,
      contactName,
      description: `Please repair my tap. My name is ${variants.join("; also ")}.`,
    },
    {
      databasePath: "unused-mocked-draft-database",
      baseURL: "http://127.0.0.1:3000",
      aiKey: "synthetic-mocked-key",
      aiURL: "https://mock.invalid/draft",
      aiModel: "mock-model",
      aiFetch: (async (_url, options) => {
        calls++;
        const serialized = String(options?.body);
        const body = JSON.parse(serialized) as {
          messages: { role: string; content: string }[];
        };
        const content = JSON.parse(
          body.messages.find((message) => message.role === "user")!.content,
        ) as { description: string; service: string };
        for (const variant of variants) {
          assert.ok(
            !serialized.toLowerCase().includes(variant.toLowerCase()),
            "Known contact name must be absent from the outgoing provider body",
          );
        }
        assert.ok(content.description.includes("Please repair my tap."));
        assert.equal(content.service, "Plumbing repairs");
        assert.equal(
          content.description.split("[name removed]").length - 1,
          variants.length,
        );
        assert.ok(!("contactName" in content));
        return new Response(
          JSON.stringify({
            choices: [
              {
                message: {
                  content: JSON.stringify({
                    reply: "Thank you. We will review the tap repair details.",
                    questions: [],
                  }),
                },
              },
            ],
          }),
        );
      }) as typeof fetch,
    },
  );
  assert.equal(calls, 1);
  assert.equal(result.source, "configured-ai");
  assert.equal(result.reviewRequired, true);
}

test("AUD-001: configured provider redacts known contact name despite capitalization", async () => {
  // Exact independent failing case first, plus all occurrences in one description.
  await assertPrivateProviderPayload("Jamie Morgan", ["jamie morgan"]);
  await assertPrivateProviderPayload("Jamie Morgan", [
    "Jamie Morgan",
    "jamie morgan",
    "JAMIE MORGAN",
    "jAmIe mOrGaN",
  ]);
});

test("configured provider matches contact names literally and includes short valid names", async () => {
  await assertPrivateProviderPayload("Jo (Jamie) Morgan+", [
    "jo (jamie) morgan+",
    "JO (JAMIE) MORGAN+",
  ]);
  await assertPrivateProviderPayload("Li", ["li", "LI"]);
  await assertPrivateProviderPayload("Élodie Martin", [
    "élodie martin",
    "ÉLODIE MARTIN",
  ]);
});
