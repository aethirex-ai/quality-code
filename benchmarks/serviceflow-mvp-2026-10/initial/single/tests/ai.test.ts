import { describe, it, expect, vi } from "vitest";
import { generateDraft, configuredDraft, draftInput } from "../src/server/ai";
import type { RequestDetail } from "../src/shared/contracts";
const request = {
  id: "private-id",
  customerId: "owner",
  serviceName: "Small repairs",
  serviceDescription: "Shelves and fittings.",
  servicePrice: "From £45",
  description:
    "Fix shelves. My email is personal@example.com and phone +44 7700 900123.",
  preferredFrom: "2030-01-10",
  preferredTo: "2030-01-12",
  contactName: "Secret Name",
  contactEmail: "secret@demo.local",
  contactPhone: "07700 900888",
  location: "private street",
  status: "New",
  version: 0,
  history: [],
} as unknown as RequestDetail;
const settings = {
  key: "synthetic-test-key-never-live",
  model: "mock-configured-model",
};
describe("Unsent reply drafting", () => {
  it("runs deterministic fallback without invoking transport", async () => {
    const transport = vi.fn();
    const draft = await generateDraft(request, {}, transport);
    expect(transport).not.toHaveBeenCalled();
    expect(draft.source).toBe("deterministic");
    expect(draft.notice).toContain("Nothing has been sent");
    expect(draft.text.match(/\?/g)?.length).toBeLessThanOrEqual(3);
    expect(draft.text).toContain("not a confirmed appointment");
    expect(draft.text).not.toContain("Secret Name");
  });
  it("asks only relevant missing-information questions", async () => {
    const draft = await generateDraft({
      ...request,
      description:
        "Room size 20 square metres. Parking access is available. Paint materials are supplied.",
    });
    expect(draft.text).not.toContain("?");
  });
  it("minimizes and redacts provider input", () => {
    const input = draftInput(request);
    expect(Object.keys(input).sort()).toEqual(
      ["datePreference", "service", "serviceDescription", "work"].sort(),
    );
    expect(JSON.stringify(input)).not.toMatch(
      /personal@example|7700|secret@|Secret Name|private street|owner/,
    );
  });
  it("uses a configured server adapter with a mocked request", async () => {
    const transport = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            choices: [
              {
                message: {
                  content: JSON.stringify({
                    reply: "Thank you for your repairs enquiry.",
                    questions: ["What size are the shelves?"],
                  }),
                },
              },
            ],
          }),
          { status: 200 },
        ),
    ) as unknown as typeof fetch;
    const draft = await generateDraft(request, settings, transport);
    expect(draft.source).toBe("ai");
    expect(draft.notice).toContain("Review");
    expect(transport).toHaveBeenCalledOnce();
    const [url, options] = (transport as unknown as ReturnType<typeof vi.fn>)
      .mock.calls[0];
    expect(url).toBe("https://api.openai.com/v1/chat/completions");
    expect(options.headers.Authorization).toBe("Bearer " + settings.key);
    const body = JSON.parse(options.body);
    expect(body.model).toBe(settings.model);
    expect(options.body).not.toContain(settings.key);
    expect(options.body).not.toMatch(
      /Secret Name|secret@demo.local|private street|personal@example/,
    );
    expect(draft.text).toContain("What size");
  });
  it("rejects invalid configured output and falls back without leaking errors", async () => {
    for (const output of [
      { choices: [] },
      { choices: [{ message: { content: "not json" } }] },
      {
        choices: [
          {
            message: {
              content: JSON.stringify({
                reply: "Test",
                questions: ["1", "2", "3", "4"],
              }),
            },
          },
        ],
      },
    ]) {
      const transport = vi.fn(
        async () => new Response(JSON.stringify(output)),
      ) as unknown as typeof fetch;
      const draft = await generateDraft(request, settings, transport);
      expect(draft.source).toBe("deterministic");
      expect(draft.notice).toContain("unavailable");
      expect(JSON.stringify(draft)).not.toContain(settings.key);
    }
  });
  it("rejects extra questions hidden in the reply body", async () => {
    const transport = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            choices: [
              {
                message: {
                  content: JSON.stringify({
                    reply: "What size? Which material? Access? Parking?",
                    questions: [],
                  }),
                },
              },
            ],
          }),
        ),
    ) as unknown as typeof fetch;
    const draft = await generateDraft(request, settings, transport);
    expect(draft.source).toBe("deterministic");
    expect(draft.notice).toContain("unavailable");
  });
  it("handles provider error, timeout and incomplete settings safely", async () => {
    const transport = vi.fn(async () => {
      throw new Error("secret backend error " + settings.key);
    }) as unknown as typeof fetch;
    expect((await generateDraft(request, settings, transport)).source).toBe(
      "deterministic",
    );
    const status = vi.fn(
      async () => new Response("private upstream trace", { status: 429 }),
    ) as unknown as typeof fetch;
    expect((await generateDraft(request, settings, status)).notice).toContain(
      "unavailable",
    );
    const unused = vi.fn();
    expect(
      (await generateDraft(request, { key: settings.key }, unused)).notice,
    ).toContain("incomplete");
    expect(unused).not.toHaveBeenCalled();
  });
  it("validates concise adapter output", async () => {
    const transport = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            choices: [
              {
                message: {
                  content: JSON.stringify({
                    reply: "x".repeat(1801),
                    questions: [],
                  }),
                },
              },
            ],
          }),
        ),
    ) as unknown as typeof fetch;
    await expect(
      configuredDraft(draftInput(request), settings, transport),
    ).rejects.toThrow();
  });
});
