import { useState, useRef, type FormEvent } from "react";
import { Plus, Pencil, Trash2, X, Check } from "lucide-react";
import { api, mutate, ApiError } from "./api";
import {
  Button,
  Field,
  Notice,
  PageIntro,
  ServiceIcon,
  useResource,
  Loading,
  Empty,
  dateTime,
} from "./components";
import {
  serviceSchema,
  type Activity,
  type Service,
  type User,
} from "../shared/contracts";
const blank = {
  name: "",
  description: "",
  price: "",
  category: "repair" as Service["category"],
  active: true,
};
export function Catalogue({ user }: { user: User }) {
  const resource = useResource(
      () => api<Service[]>("/admin/services"),
      [user.id],
    ),
    activity = useResource(() => api<Activity[]>("/admin/activity"), [user.id]);
  const [editor, setEditor] = useState<Service | "new" | null>(null),
    [form, setForm] = useState(blank),
    [fields, setFields] = useState<Record<string, string>>({}),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [confirm, setConfirm] = useState<string | null>(null);
  const editorRef = useRef<HTMLDivElement>(null);
  function edit(s: Service | "new") {
    setEditor(s);
    setForm(s === "new" ? blank : s);
    setFields({});
    setError("");
    setConfirm(null);
    setTimeout(() => {
      editorRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      editorRef.current?.querySelector<HTMLInputElement>("input")?.focus();
    }, 0);
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");
    const v = serviceSchema.safeParse(form);
    if (!v.success) {
      setFields(
        Object.fromEntries(v.error.issues.map((i) => [i.path[0], i.message])),
      );
      setError("Please check the highlighted service fields.");
      return;
    }
    setBusy(true);
    try {
      const result = await mutate<Service>(
        user.id,
        editor === "new" ? "/services" : "/services/" + (editor as Service).id,
        editor === "new" ? "POST" : "PATCH",
        editor === "new"
          ? v.data
          : { ...v.data, version: (editor as Service).version },
      );
      resource.setData(prevList(resource.data, result));
      setEditor(null);
      setNotice(
        "Service saved. Existing requests retain their original service details.",
      );
      void activity.reload();
    } catch (e) {
      setError((e as Error).message);
      setFields((e as ApiError).fields || {});
    } finally {
      setBusy(false);
    }
  }
  async function remove(s: Service) {
    setBusy(true);
    setError("");
    try {
      await mutate(user.id, "/services/" + s.id, "DELETE", {
        version: s.version,
      });
      resource.setData(resource.data!.filter((x) => x.id !== s.id));
      setConfirm(null);
      setNotice(
        "Service deleted. Its catalogue action is retained in the activity log.",
      );
      void activity.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function toggle(s: Service) {
    setBusy(true);
    setError("");
    try {
      const result = await mutate<Service>(
        user.id,
        "/services/" + s.id,
        "PATCH",
        { ...s, active: !s.active },
      );
      resource.setData(prevList(resource.data, result));
      setNotice(
        result.active
          ? "Service activated. Customers can select it."
          : "Service deactivated. Existing enquiries are preserved.",
      );
      void activity.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function prevList(list: Service[] | null, s: Service) {
    return list?.some((x) => x.id === s.id)
      ? list.map((x) => (x.id === s.id ? s : x))
      : [...(list || []), s];
  }
  const inputAttrs = (name: "name" | "description" | "price") => ({
    id: "service-" + name,
    value: form[name],
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm({ ...form, [name]: e.target.value }),
    "aria-invalid": !!fields[name],
    "aria-describedby": fields[name] ? "service-" + name + "-error" : undefined,
  });
  return (
    <>
      <PageIntro
        eyebrow="ADMINISTRATION"
        title="A considered service catalogue."
        action={
          <Button
            className="button"
            onClick={() => edit("new")}
            disabled={busy}
          >
            <Plus size={18} /> Add service
          </Button>
        }
      >
        Keep services clear and current. Deactivation preserves every enquiry
        and removes a service from new requests.
      </PageIntro>
      {notice && <Notice>{notice}</Notice>}
      {(error || resource.error) && (
        <Notice error>
          {error || resource.error}{" "}
          <Button
            className="text-link"
            onClick={() => {
              void resource.reload();
              setEditor(null);
              setError("");
            }}
          >
            Reload catalogue
          </Button>
        </Notice>
      )}
      {editor && (
        <div className="panel service-editor" ref={editorRef}>
          <div className="section-title">
            <h2>
              {editor === "new" ? "Create a service" : "Edit " + editor.name}
            </h2>
            <Button
              className="icon-button"
              aria-label="Close service editor"
              onClick={() => setEditor(null)}
              disabled={busy}
            >
              <X size={20} />
            </Button>
          </div>
          <form noValidate onSubmit={save}>
            <div className="two-columns">
              <Field
                label="Service name"
                name="service-name"
                error={fields.name}
              >
                <input {...inputAttrs("name")} required maxLength={80} />
              </Field>
              <Field
                label="Indicative price"
                name="service-price"
                error={fields.price}
              >
                <input
                  {...inputAttrs("price")}
                  required
                  maxLength={80}
                  placeholder="From £45 or Request a quote"
                />
              </Field>
            </div>
            <Field
              label="Useful description"
              name="service-description"
              error={fields.description}
            >
              <textarea
                {...inputAttrs("description")}
                rows={3}
                required
                maxLength={600}
              />
            </Field>
            <div className="two-columns">
              <Field label="Category" name="service-category">
                <select
                  id="service-category"
                  value={form.category}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      category: e.target.value as Service["category"],
                    })
                  }
                >
                  <option value="repair">Repairs</option>
                  <option value="garden">Garden care</option>
                  <option value="painting">Painting</option>
                  <option value="cleaning">Cleaning</option>
                </select>
              </Field>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.active}
                  onChange={(e) =>
                    setForm({ ...form, active: e.target.checked })
                  }
                />{" "}
                Active · available for new requests
              </label>
            </div>
            <Button className="button" busy={busy}>
              <Check size={17} /> Save service
            </Button>
          </form>
        </div>
      )}
      {resource.loading && !resource.data ? (
        <Loading />
      ) : resource.data?.length ? (
        <div className="admin-service-grid">
          {resource.data.map((s) => (
            <article
              className={"panel admin-service " + (!s.active ? "inactive" : "")}
              key={s.id}
            >
              <div className="request-card-top">
                <span className={"service-icon " + s.category}>
                  <ServiceIcon category={s.category} />
                </span>
                <span className={"availability " + (s.active ? "active" : "")}>
                  {s.active ? "Active" : "Inactive"}
                </span>
              </div>
              <h2>{s.name}</h2>
              <p>{s.description}</p>
              <strong>{s.price}</strong>
              <div className="service-controls">
                <Button
                  className="button secondary small-button"
                  onClick={() => edit(s)}
                  disabled={busy}
                >
                  <Pencil size={15} /> Edit
                </Button>
                <Button
                  className="text-link"
                  onClick={() => toggle(s)}
                  disabled={busy}
                >
                  {s.active ? "Deactivate" : "Activate"}
                </Button>
                <Button
                  className="icon-button"
                  onClick={() => setConfirm(s.id)}
                  disabled={busy}
                  aria-label={"Delete " + s.name}
                >
                  <Trash2 size={17} />
                </Button>
              </div>
              {confirm === s.id && (
                <div className="delete-confirm">
                  <p>
                    Delete this service? Services with request history cannot be
                    deleted.
                  </p>
                  <Button
                    className="button danger small-button"
                    busy={busy}
                    onClick={() => remove(s)}
                  >
                    Confirm delete
                  </Button>
                  <Button
                    className="text-link"
                    disabled={busy}
                    onClick={() => setConfirm(null)}
                  >
                    Cancel
                  </Button>
                </div>
              )}
            </article>
          ))}
        </div>
      ) : (
        <Empty title="No services yet">
          Add a service to make it available to customers.
        </Empty>
      )}
      <section className="panel catalogue-history">
        <div className="section-title">
          <h2>Catalogue activity</h2>
          <span className="small-label">SAVED WITH EVERY CHANGE</span>
        </div>
        {activity.error && (
          <Notice error>
            {activity.error}{" "}
            <Button onClick={activity.reload}>Retry activity</Button>
          </Notice>
        )}
        {activity.data?.length ? (
          <ol className="catalogue-log">
            {activity.data.map((a) => (
              <li key={a.id}>
                <strong>{a.action}</strong>
                <span>
                  {a.actorName} · {dateTime(a.createdAt)}
                </span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="subtle">
            No catalogue changes yet. Create, edit, activate or delete a service
            to see its history here.
          </p>
        )}
      </section>
    </>
  );
}
