// @vitest-environment jsdom
import { createElement as h } from "react";
import {
  render,
  cleanup,
  screen,
  fireEvent,
  act,
} from "@testing-library/react";
import {
  MemoryRouter,
  Routes,
  Route,
  useNavigate,
  type NavigateFunction,
} from "react-router-dom";
import { beforeEach, afterEach, it, expect, vi } from "vitest";
import { Detail } from "../src/client/detail";
import { RequestForm } from "../src/client/forms";
import { useResource } from "../src/client/components";
import { api, mutate } from "../src/client/api";
import type {
  User,
  RequestDetail,
  Draft,
  Service,
} from "../src/shared/contracts";
vi.mock("../src/client/api", () => ({
  api: vi.fn(),
  mutate: vi.fn(),
  authClient: {},
}));
const apiMock = vi.mocked(api),
  mutationMock = vi.mocked(mutate);
const staff: User = {
  id: "demo-provider",
  name: "Sam Green",
  email: "provider@demo.local",
  role: "provider",
};
const admin: User = {
  id: "demo-admin",
  name: "Robin Ellis",
  email: "admin@demo.local",
  role: "admin",
};
const customer: User = {
  id: "demo-alex",
  name: "Alex Morgan",
  email: "alex@demo.local",
  role: "customer",
};
const request = (id: string, serviceName = "Small repairs"): RequestDetail => ({
  id,
  customerId: customer.id,
  serviceId: "small-repairs",
  serviceName,
  serviceDescription: "Useful help with everyday home repairs.",
  servicePrice: "From £45",
  description: "Two cupboard hinges need repair.",
  location: "BS3 1AB",
  preferredFrom: "2030-01-15",
  preferredTo: "",
  contactName: customer.name,
  contactEmail: customer.email,
  contactPhone: "07700 900123",
  status: "New",
  version: 0,
  createdAt: "2026-10-14T10:00:00Z",
  updatedAt: "2026-10-14T10:00:00Z",
  history: [
    {
      id: 1,
      requestId: id,
      actorName: customer.name,
      action: "Request submitted",
      createdAt: "2026-10-14T10:00:00Z",
    },
  ],
});
const a = request("A"),
  b = request("B", "Garden care");
const reply = (text: string): Draft => ({
  source: "deterministic",
  notice: "Demo-generated. Review; nothing sent.",
  text,
});
function deferred<T>() {
  let resolve!: (value: T) => void, reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
let navigate: NavigateFunction;
function View({ user }: { user: User }) {
  navigate = useNavigate();
  return h(Detail, { user });
}
function tree(user = staff) {
  return h(
    MemoryRouter,
    { initialEntries: ["/requests/A"] },
    h(
      Routes,
      null,
      h(Route, { path: "/requests/:id", element: h(View, { user }) }),
    ),
  );
}
const detailStatus = () =>
  document.querySelector(".detail-heading > .status")?.textContent;
async function openDetail() {
  const ui = render(tree());
  await screen.findByRole("heading", { name: "Small repairs", level: 1 });
  return ui;
}
beforeEach(() => {
  vi.resetAllMocks();
  sessionStorage.clear();
  apiMock.mockImplementation(async (path) => (path === "/requests/A" ? a : b));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("AUD-002: an older pre-save read cannot overwrite the committed Detail status/history", async () => {
  await openDetail();
  const oldRead = deferred<RequestDetail>(),
    saved = deferred<RequestDetail>();
  apiMock.mockReturnValue(oldRead.promise);
  mutationMock.mockReturnValue(saved.promise);
  fireEvent.click(
    screen.getByRole("button", { name: "Reload latest details" }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Mark as Reviewing" }));
  await act(async () =>
    saved.resolve({
      ...a,
      status: "Reviewing",
      version: 1,
      history: [
        ...a.history,
        {
          id: 2,
          requestId: "A",
          actorName: staff.name,
          action: "Status changed: New → Reviewing",
          createdAt: a.createdAt,
        },
      ],
    }),
  );
  expect(detailStatus()).toBe("Reviewing");
  await act(async () => oldRead.resolve(a));
  expect(detailStatus()).toBe("Reviewing");
  expect(screen.getByText("Status changed: New → Reviewing")).toBeTruthy();
  expect(
    screen.getByText("Status updated and saved to the request history."),
  ).toBeTruthy();
});

it.each(["resolve", "reject"])(
  "AUD-002: out-of-order owner read %s cannot affect the current owner",
  async (outcome) => {
    const reads = {
      A: deferred<{ owner: string }>(),
      B: deferred<{ owner: string }>(),
    };
    function Resource({ owner }: { owner: "A" | "B" }) {
      const result = useResource(() => reads[owner].promise, [owner]);
      return h(
        "p",
        { "data-testid": "resource" },
        JSON.stringify({
          owner,
          data: result.data,
          error: result.error,
          loading: result.loading,
        }),
      );
    }
    const ui = render(h(Resource, { owner: "A" }));
    ui.rerender(h(Resource, { owner: "B" }));
    await act(async () => reads.B.resolve({ owner: "B" }));
    await act(async () =>
      outcome === "resolve"
        ? reads.A.resolve({ owner: "A" })
        : reads.A.reject(new Error("Old owner's read failed")),
    );
    expect(JSON.parse(screen.getByTestId("resource").textContent!)).toEqual({
      owner: "B",
      data: { owner: "B" },
      error: "",
      loading: false,
    });
  },
);

it("AUD-002: an already loaded previous owner is hidden during the next owner's load", async () => {
  const next = deferred<{ owner: string }>();
  function Resource({ owner }: { owner: string }) {
    const result = useResource(
      () => (owner === "A" ? Promise.resolve({ owner }) : next.promise),
      [owner],
    );
    return h("p", { "data-testid": "resource" }, JSON.stringify(result.data));
  }
  const ui = render(h(Resource, { owner: "A" }));
  await act(async () => {});
  ui.rerender(h(Resource, { owner: "B" }));
  expect(screen.getByTestId("resource").textContent).toBe("null");
});

it.each(["request", "actor"])(
  "AUD-003: changing %s resets editable draft, review, copy and decline state",
  async (identity) => {
    apiMock.mockImplementation(async (path) =>
      path.endsWith("/draft")
        ? reply("Reply specifically for customer A repairs")
        : path === "/requests/A"
          ? a
          : b,
    );
    const ui = await openDetail();
    fireEvent.click(screen.getByRole("button", { name: "Draft reply" }));
    await screen.findByLabelText("Editable reply draft");
    fireEvent.change(screen.getByLabelText("Editable reply draft"), {
      target: { value: "Edited A reply" },
    });
    fireEvent.click(
      screen.getByLabelText("I’ve reviewed the details and wording."),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Decline this enquiry" }),
    );
    if (identity === "request")
      await act(async () => {
        await navigate("/requests/B");
      });
    else ui.rerender(tree(admin));
    await screen.findByRole("heading", {
      name: identity === "request" ? "Garden care" : "Small repairs",
      level: 1,
    });
    expect(screen.queryByLabelText("Editable reply draft")).toBeNull();
    expect(
      screen.queryByLabelText("I’ve reviewed the details and wording."),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Confirm decline" }),
    ).toBeNull();
    expect(screen.getByRole("button", { name: "Draft reply" })).toBeTruthy();
  },
);

it.each(["resolve", "reject"])(
  "AUD-003: delayed previous draft %s cannot replace or error the current request's draft",
  async (outcome) => {
    const oldDraft = deferred<Draft>();
    apiMock.mockImplementation(async (path) =>
      path === "/requests/A/draft"
        ? oldDraft.promise
        : path === "/requests/B/draft"
          ? reply("Current B garden reply")
          : path === "/requests/A"
            ? a
            : b,
    );
    await openDetail();
    fireEvent.click(screen.getByRole("button", { name: "Draft reply" }));
    await act(async () => {
      await navigate("/requests/B");
    });
    await screen.findByRole("heading", { name: "Garden care", level: 1 });
    fireEvent.click(screen.getByRole("button", { name: "Draft reply" }));
    await screen.findByLabelText("Editable reply draft");
    await act(async () =>
      outcome === "resolve"
        ? oldDraft.resolve(reply("Old A reply"))
        : oldDraft.reject(new Error("Previous A draft failed")),
    );
    expect(
      (screen.getByLabelText("Editable reply draft") as HTMLTextAreaElement)
        .value,
    ).toBe("Current B garden reply");
    expect(screen.queryByText("Previous A draft failed")).toBeNull();
  },
);

it("AUD-003: a previous status completion cannot replace the new request or display a saved message", async () => {
  const saved = deferred<RequestDetail>();
  mutationMock.mockReturnValue(saved.promise);
  await openDetail();
  fireEvent.click(screen.getByRole("button", { name: "Mark as Reviewing" }));
  await act(async () => {
    await navigate("/requests/B");
  });
  await screen.findByRole("heading", { name: "Garden care", level: 1 });
  await act(async () =>
    saved.resolve({ ...a, status: "Reviewing", version: 1 }),
  );
  expect(
    screen.getByRole("heading", { name: "Garden care", level: 1 }),
  ).toBeTruthy();
  expect(detailStatus()).toBe("New");
  expect(
    screen.queryByText("Status updated and saved to the request history."),
  ).toBeNull();
});

it("AUD-003: a previous clipboard failure cannot select the new request's textarea or show its copy message", async () => {
  const clipboard = deferred<void>();
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText: () => clipboard.promise },
  });
  apiMock.mockImplementation(async (path) =>
    path.endsWith("/draft")
      ? reply(path.includes("/A/") ? "A reply" : "B reply")
      : path === "/requests/A"
        ? a
        : b,
  );
  await openDetail();
  fireEvent.click(screen.getByRole("button", { name: "Draft reply" }));
  await screen.findByLabelText("Editable reply draft");
  fireEvent.click(
    screen.getByLabelText("I’ve reviewed the details and wording."),
  );
  fireEvent.click(screen.getByRole("button", { name: "Copy reviewed draft" }));
  await act(async () => {
    await navigate("/requests/B");
  });
  await screen.findByRole("heading", { name: "Garden care", level: 1 });
  fireEvent.click(screen.getByRole("button", { name: "Draft reply" }));
  await screen.findByLabelText("Editable reply draft");
  await act(async () => clipboard.reject(new Error("Clipboard interrupted")));
  expect(screen.queryByText(/Clipboard unavailable/)).toBeNull();
  expect(
    (screen.getByLabelText("Editable reply draft") as HTMLTextAreaElement)
      .value,
  ).toBe("B reply");
});

it("AUD-001: an uncertain save keeps the actual request form and its tab-scoped draft intact", async () => {
  const service: Service = {
    id: "small-repairs",
    name: "Small repairs",
    description: "Useful help with everyday home repairs.",
    price: "From £45",
    category: "repair",
    active: true,
    version: 0,
  };
  apiMock.mockResolvedValue([service]);
  mutationMock.mockRejectedValue(
    new Error("The saved response was unreadable. Retry this request."),
  );
  render(h(MemoryRouter, null, h(RequestForm, { user: customer })));
  await screen.findByRole("option", { name: "Small repairs · From £45" });
  const fields = {
    serviceId: service.id,
    description: a.description,
    location: a.location,
    preferredFrom: a.preferredFrom,
    contactName: customer.name,
    contactEmail: customer.email,
    contactPhone: a.contactPhone,
  };
  for (const [id, value] of Object.entries(fields))
    fireEvent.change(document.getElementById(id)!, { target: { value } });
  fireEvent.click(screen.getByRole("button", { name: "Submit request" }));
  await screen.findByRole("alert");
  for (const [id, value] of Object.entries(fields))
    expect((document.getElementById(id) as HTMLInputElement).value).toBe(value);
  expect(
    JSON.parse(sessionStorage.getItem("request-form:" + customer.id)!),
  ).toMatchObject(fields);
});
