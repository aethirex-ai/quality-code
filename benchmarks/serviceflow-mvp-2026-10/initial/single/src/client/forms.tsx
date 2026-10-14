import { useState, useRef, useEffect, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowRight,
  ShieldCheck,
  CalendarDays,
  ClipboardList,
} from "lucide-react";
import { api, authClient, mutate, ApiError } from "./api";
import {
  Button,
  Field,
  Notice,
  PageIntro,
  ServiceIcon,
  useResource,
  Loading,
} from "./components";
import {
  requestSchema,
  type User,
  type Service,
  type RequestDetail,
} from "../shared/contracts";
export function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const navigate = useNavigate(),
    [params] = useSearchParams();
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await authClient.signIn.email({
        email: email.trim().toLowerCase(),
        password,
      });
      if (result.error)
        throw new Error(
          result.error.message || "Sign-in failed. Check your details.",
        );
      const user = await api<User>("/me");
      onLogin(user);
      navigate(
        user.role === "customer" && params.get("next") === "request"
          ? "/request"
          : "/dashboard",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-layout container">
      <div className="login-story">
        <div className="eyebrow">YOUR HOME, IN GOOD HANDS</div>
        <h1>
          A little less
          <br /> on your list.
        </h1>
        <p>
          Sign in to request a service and follow each step, from your first
          enquiry to the finishing touches.
        </p>
        <div className="login-illustration">
          <ClipboardList size={76} strokeWidth={1} />
          <span>
            One place.
            <br />
            Every little detail.
          </span>
        </div>
        <p className="subtle">
          ServiceFlow is a portfolio demo. All accounts and enquiries are
          fictional.
        </p>
      </div>
      <div className="panel login-panel">
        <div className="eyebrow">WELCOME BACK</div>
        <h2>Sign in to your account</h2>
        <p className="subtle">Customers and team members sign in here.</p>
        <form onSubmit={submit}>
          {error && <Notice error>{error}</Notice>}
          <Field label="Email address" name="email">
            <input
              id="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              maxLength={160}
            />
          </Field>
          <Field label="Password" name="password">
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </Field>
          <Button className="button full" busy={busy}>
            Sign in <ArrowRight size={18} />
          </Button>
        </form>
        <details className="demo-accounts">
          <summary>Explore with a demo account</summary>
          <p>
            Password for all accounts: <code>ServiceFlow2026!</code>
          </p>
          {[
            { email: "alex@demo.local", role: "Customer · Alex" },
            { email: "jamie@demo.local", role: "Customer · Jamie" },
            { email: "provider@demo.local", role: "Provider · Sam" },
            { email: "admin@demo.local", role: "Admin · Robin" },
          ].map((a) => (
            <button
              type="button"
              className="demo-account"
              key={a.email}
              onClick={() => {
                setEmail(a.email);
                setPassword("ServiceFlow2026!");
              }}
            >
              <span>{a.role}</span>
              <small>{a.email}</small>
              <ArrowRight size={16} />
            </button>
          ))}
        </details>
        <div className="secure-note">
          <ShieldCheck size={17} /> Demo accounts only. No registration or email
          sending.
        </div>
      </div>
    </div>
  );
}
const blank = {
  serviceId: "",
  description: "",
  location: "",
  preferredFrom: "",
  preferredTo: "",
  contactName: "",
  contactEmail: "",
  contactPhone: "",
};
export function RequestForm({ user }: { user: User }) {
  const [params] = useSearchParams(),
    navigate = useNavigate(),
    slot = "request-form:" + user.id;
  const [form, setForm] = useState(() => {
    try {
      return {
        ...blank,
        contactName: user.name,
        contactEmail: user.email,
        ...JSON.parse(sessionStorage.getItem(slot) || "{}"),
        ...(params.get("service") ? { serviceId: params.get("service") } : {}),
      };
    } catch {
      return { ...blank, contactName: user.name, contactEmail: user.email };
    }
  });
  const [fields, setFields] = useState<Record<string, string>>({}),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const formRef = useRef<HTMLFormElement>(null),
    {
      data: services,
      error: loadError,
      reload,
    } = useResource(() => api<Service[]>("/services"));
  useEffect(() => {
    sessionStorage.setItem(slot, JSON.stringify(form));
  }, [form, slot]);
  function update(name: string, value: string) {
    setForm((f: typeof blank) => ({ ...f, [name]: value }));
    setFields((f) => ({ ...f, [name]: "" }));
  }
  const attrs = (name: keyof typeof blank) => ({
    id: name,
    name,
    value: form[name],
    onChange: (
      e: React.ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ) => update(name, e.target.value),
    "aria-invalid": !!fields[name],
    "aria-describedby": fields[name] ? name + "-error" : undefined,
  });
  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setFields({});
    const validation = requestSchema.safeParse(form);
    if (!validation.success) {
      const errors = Object.fromEntries(
        validation.error.issues.map((i) => [i.path[0], i.message]),
      );
      setFields(errors);
      setError("Please check the highlighted fields.");
      setTimeout(
        () =>
          formRef.current
            ?.querySelector<HTMLElement>('[aria-invalid="true"]')
            ?.focus(),
        0,
      );
      return;
    }
    setBusy(true);
    try {
      const result = await mutate<RequestDetail>(
        user.id,
        "/requests",
        "POST",
        validation.data,
      );
      sessionStorage.removeItem(slot);
      navigate("/requests/" + result.id, { state: { submitted: true } });
    } catch (e) {
      const issue = e as ApiError;
      setError(issue.message);
      setFields(issue.fields || {});
    } finally {
      setBusy(false);
    }
  }
  const selected = services?.find((s) => s.id === form.serviceId);
  return (
    <div className="container request-page">
      <Link className="back-link" to="/dashboard">
        ← Back to your requests
      </Link>
      <PageIntro eyebrow="LET’S GET THE DETAILS" title="Request a little help">
        Tell us about the job. We’ll review your enquiry before discussing a
        quote or booking.
      </PageIntro>
      <div className="form-layout">
        <form
          className="panel request-form"
          noValidate
          onSubmit={submit}
          ref={formRef}
        >
          {error && <Notice error>{error}</Notice>}
          {loadError && (
            <Notice error>
              {loadError}{" "}
              <button type="button" onClick={reload}>
                Reload services
              </button>
            </Notice>
          )}
          <div className="form-section-title">
            <span>01</span>
            <h2>The job</h2>
          </div>
          <Field
            label="What can we help with?"
            name="serviceId"
            error={fields.serviceId}
          >
            <select {...attrs("serviceId")} required>
              <option value="">Choose a service</option>
              {services?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} · {s.price}
                </option>
              ))}
            </select>
          </Field>
          <Field
            label="Tell us what needs doing"
            name="description"
            error={fields.description}
            hint="A few specifics help us understand the size and scope of the job. Please keep contact details in the fields below."
          >
            <textarea
              {...attrs("description")}
              rows={4}
              required
              minLength={12}
              maxLength={2000}
              placeholder="For example, two loose cupboard hinges and a shelf to fit…"
            />
          </Field>
          <Field
            label="Postcode or location"
            name="location"
            error={fields.location}
          >
            <input
              {...attrs("location")}
              required
              maxLength={160}
              autoComplete="postal-code"
              placeholder="For example, BS3 1AB, South Bristol"
            />
          </Field>
          <div className="form-section-title">
            <span>02</span>
            <h2>Your preferred dates</h2>
          </div>
          <p className="subtle">
            A date preference, not a confirmed appointment.
          </p>
          <div className="two-columns">
            <Field
              label="Preferred date / from"
              name="preferredFrom"
              error={fields.preferredFrom}
            >
              <input
                {...attrs("preferredFrom")}
                type="date"
                min={new Date().toISOString().slice(0, 10)}
                required
              />
            </Field>
            <Field
              label="Until (optional)"
              name="preferredTo"
              error={fields.preferredTo}
            >
              <input
                {...attrs("preferredTo")}
                type="date"
                min={
                  form.preferredFrom || new Date().toISOString().slice(0, 10)
                }
              />
            </Field>
          </div>
          <div className="form-section-title">
            <span>03</span>
            <h2>How to reach you</h2>
          </div>
          <Field
            label="Contact name"
            name="contactName"
            error={fields.contactName}
          >
            <input
              {...attrs("contactName")}
              required
              maxLength={100}
              autoComplete="name"
            />
          </Field>
          <div className="two-columns">
            <Field
              label="Email address"
              name="contactEmail"
              error={fields.contactEmail}
            >
              <input
                {...attrs("contactEmail")}
                required
                type="email"
                maxLength={160}
                autoComplete="email"
              />
            </Field>
            <Field
              label="Phone number"
              name="contactPhone"
              error={fields.contactPhone}
            >
              <input
                {...attrs("contactPhone")}
                required
                type="tel"
                maxLength={30}
                autoComplete="tel"
                placeholder="07700 900123"
              />
            </Field>
          </div>
          <div className="form-submit">
            <p className="subtle">
              Submitting starts an enquiry. No payment or appointment is
              confirmed.
            </p>
            <Button className="button" busy={busy} disabled={!services?.length}>
              Submit request <ArrowRight size={18} />
            </Button>
          </div>
        </form>
        <aside className="request-aside">
          <div className="panel selected-service">
            <div className="eyebrow">YOUR SERVICE</div>
            <span className="service-icon">
              <ServiceIcon
                category={selected?.category || "repair"}
                size={30}
              />
            </span>
            <h2>{selected?.name || "A little help starts here."}</h2>
            <p>
              {selected?.description ||
                "Choose the service that best fits the job. Add the details and we’ll take a closer look."}
            </p>
            {selected && (
              <strong className="selected-price">{selected.price}</strong>
            )}
            <small>
              Indicative pricing. A final quote depends on the scope.
            </small>
          </div>
          <div className="aside-info">
            <CalendarDays size={22} />
            <div>
              <strong>What happens next?</strong>
              <p>
                Your enquiry starts as New. Track the review, quote and any
                agreed booking in your dashboard.
              </p>
            </div>
          </div>
          <div className="aside-info">
            <ShieldCheck size={22} />
            <div>
              <strong>Your details stay with your request.</strong>
              <p>
                Only you and the authorised service team can view your enquiry.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
