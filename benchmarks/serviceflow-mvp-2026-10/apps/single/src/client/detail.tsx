import { useState, useRef, useLayoutEffect } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  ArrowRight,
  CalendarDays,
  MapPin,
  UserRound,
  Sparkles,
  Copy,
  History,
  RefreshCw,
} from "lucide-react";
import { api, mutate } from "./api";
import {
  Button,
  Notice,
  Loading,
  StatusBadge,
  dateLabel,
  dateTime,
  useResource,
} from "./components";
import {
  statuses,
  transitions,
  type RequestDetail,
  type Draft,
  type User,
  type Status,
} from "../shared/contracts";
export function Detail({ user }: { user: User }) {
  const { id } = useParams();
  // The route component may stay mounted. Its editable/action state belongs
  // to exactly one request and actor, including the actor's current role.
  return (
    <RequestDetailView
      key={JSON.stringify([id, user.id, user.role])}
      user={user}
    />
  );
}
function RequestDetailView({ user }: { user: User }) {
  const { id } = useParams(),
    location = useLocation(),
    {
      data: r,
      setData,
      error,
      loading,
      reload,
    } = useResource(() => api<RequestDetail>("/requests/" + id), [id, user.id]);
  const [actionError, setActionError] = useState(""),
    [saved, setSaved] = useState(""),
    [busy, setBusy] = useState(false),
    [decline, setDecline] = useState(false),
    [draft, setDraft] = useState<Draft | null>(null),
    [draftBusy, setDraftBusy] = useState(false),
    [reviewed, setReviewed] = useState(false),
    [copyState, setCopyState] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null),
    staff = user.role !== "customer";
  const active = useRef(false);
  useLayoutEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);
  async function update(status: Status) {
    if (!r) return;
    setBusy(true);
    setActionError("");
    setSaved("");
    try {
      const result = await mutate<RequestDetail>(
        user.id,
        "/requests/" + r.id + "/status",
        "PATCH",
        { status, version: r.version },
      );
      if (!active.current) return;
      setData(result);
      setDecline(false);
      setSaved("Status updated and saved to the request history.");
    } catch (e) {
      if (active.current) setActionError((e as Error).message);
    } finally {
      if (active.current) setBusy(false);
    }
  }
  async function generate() {
    if (!r) return;
    setDraftBusy(true);
    setActionError("");
    try {
      const result = await api<Draft>("/requests/" + r.id + "/draft", {
        method: "POST",
        body: "{}",
      });
      if (!active.current) return;
      setDraft(result);
      setReviewed(false);
      setCopyState("");
    } catch (e) {
      if (active.current) setActionError((e as Error).message);
    } finally {
      if (active.current) setDraftBusy(false);
    }
  }
  async function copy() {
    try {
      await navigator.clipboard.writeText(draft!.text);
      if (!active.current) return;
      setCopyState("Draft copied. Nothing has been sent.");
    } catch {
      if (!active.current) return;
      textarea.current?.focus();
      textarea.current?.select();
      setCopyState(
        "Clipboard unavailable. The draft is selected; use your device’s copy command.",
      );
    }
  }
  const reference = id?.slice(0, 8).toUpperCase();
  return (
    <>
      <Link className="back-link" to="/dashboard">
        ← Back to {staff ? "all" : "your"} requests
      </Link>
      {location.state?.submitted && (
        <Notice>
          Request received. Follow its progress here. Your preferred date is not
          a confirmed appointment.
        </Notice>
      )}
      {error && (
        <Notice error>
          {error}{" "}
          <Button className="text-link" onClick={reload}>
            Try again
          </Button>
        </Notice>
      )}
      {loading && !r ? (
        <Loading />
      ) : (
        r && (
          <>
            <div className="detail-heading">
              <div>
                <div className="eyebrow">ENQUIRY · {reference}</div>
                <h1>{r.serviceName}</h1>
                <p>
                  Submitted {dateLabel(r.createdAt)} <span>·</span>{" "}
                  {r.contactName}
                </p>
              </div>
              <StatusBadge status={r.status} />
            </div>
            {actionError && (
              <Notice error>
                {actionError}{" "}
                <Button
                  className="text-link"
                  onClick={() => {
                    void reload();
                    setActionError("");
                  }}
                >
                  Reload latest details
                </Button>
              </Notice>
            )}
            {saved && <Notice>{saved}</Notice>}
            <div className="workflow" aria-label="Request progress">
              {statuses
                .filter((s) => s !== "Declined")
                .map((s, i) => (
                  <div
                    className={
                      (r.status === "Declined"
                        ? ""
                        : i <= statuses.indexOf(r.status)
                          ? "done"
                          : "") + " workflow-step"
                    }
                    key={s}
                  >
                    <span>{i + 1}</span>
                    <small>{s}</small>
                  </div>
                ))}
            </div>
            {r.status === "Declined" && (
              <p className="subtle">
                This enquiry is closed as Declined. No further status changes
                are available.
              </p>
            )}
            <div className="detail-layout">
              <div className="detail-main">
                <section className="panel">
                  <div className="section-title">
                    <h2>The work, in your words</h2>
                    <span className="small-label">REQUEST DETAILS</span>
                  </div>
                  <p className="request-description">{r.description}</p>
                  <div className="detail-facts">
                    <div>
                      <MapPin />
                      <span>
                        <small>Location</small>
                        <strong>{r.location}</strong>
                      </span>
                    </div>
                    <div>
                      <CalendarDays />
                      <span>
                        <small>
                          Preferred date{r.preferredTo ? " range" : ""} · not
                          confirmed
                        </small>
                        <strong>
                          {dateLabel(r.preferredFrom)}
                          {r.preferredTo
                            ? " – " + dateLabel(r.preferredTo)
                            : ""}
                        </strong>
                      </span>
                    </div>
                  </div>
                </section>
                <section className="panel">
                  <div className="section-title">
                    <h2>Request history</h2>
                    <History size={19} />
                  </div>
                  <ol className="timeline">
                    {r.history.map((h) => (
                      <li key={h.id}>
                        <span className="timeline-dot" />
                        <div>
                          <strong>{h.action}</strong>
                          <p>
                            {h.actorName} <span>·</span>{" "}
                            <time dateTime={h.createdAt}>
                              {dateTime(h.createdAt)}
                            </time>
                          </p>
                        </div>
                      </li>
                    ))}
                  </ol>
                </section>
                {staff && (
                  <section className="panel draft-panel">
                    <div className="section-title">
                      <h2>
                        <Sparkles size={20} /> A thoughtful first reply
                      </h2>
                      <span className="small-label">DRAFT ASSISTANT</span>
                    </div>
                    <p className="subtle">
                      Start with a draft from the request details. Review it,
                      make it your own, and use it outside this demo when
                      appropriate.
                    </p>
                    <Button
                      className="button secondary"
                      onClick={generate}
                      busy={draftBusy}
                    >
                      {draft ? "Regenerate draft" : "Draft reply"}{" "}
                      <Sparkles size={17} />
                    </Button>
                    {draft && (
                      <div className="draft-content">
                        <Notice>{draft.notice}</Notice>
                        <label htmlFor="reply-draft">
                          Editable reply draft
                        </label>
                        <textarea
                          id="reply-draft"
                          ref={textarea}
                          rows={11}
                          value={draft.text}
                          onChange={(e) => {
                            setDraft({ ...draft, text: e.target.value });
                            setReviewed(false);
                            setCopyState("");
                          }}
                        />
                        <label className="checkbox-label">
                          <input
                            type="checkbox"
                            checked={reviewed}
                            onChange={(e) => setReviewed(e.target.checked)}
                          />{" "}
                          I’ve reviewed the details and wording.
                        </label>
                        <Button
                          className="button secondary"
                          onClick={copy}
                          disabled={!reviewed}
                        >
                          <Copy size={16} /> Copy reviewed draft
                        </Button>
                        {copyState && (
                          <p role="status" className="subtle">
                            {copyState}
                          </p>
                        )}
                        <small className="subtle">
                          Drafting does not change status or record a sent
                          message. This app never sends replies.
                        </small>
                      </div>
                    )}
                  </section>
                )}
              </div>
              <aside className="detail-aside">
                {staff && (
                  <section className="panel status-panel">
                    <div className="eyebrow">NEXT STEP</div>
                    <h2>Keep the request moving.</h2>
                    {transitions[r.status].length ? (
                      <>
                        <p className="subtle">
                          Only the next step is available. Each update is saved
                          with your name and time.
                        </p>
                        {transitions[r.status]
                          .filter((s) => s !== "Declined")
                          .map((s) => (
                            <Button
                              key={s}
                              className="button full"
                              busy={busy}
                              onClick={() => update(s)}
                            >
                              Mark as {s} <ArrowRight size={16} />
                            </Button>
                          ))}
                        {transitions[r.status].includes("Declined") &&
                          !decline && (
                            <Button
                              className="text-link decline-link"
                              disabled={busy}
                              onClick={() => setDecline(true)}
                            >
                              Decline this enquiry
                            </Button>
                          )}
                        {decline && (
                          <div className="decline-confirm">
                            <p>
                              This closes the enquiry permanently. Declined
                              requests cannot be reopened.
                            </p>
                            <Button
                              className="button danger"
                              busy={busy}
                              onClick={() => update("Declined")}
                            >
                              Confirm decline
                            </Button>
                            <Button
                              className="text-link"
                              onClick={() => setDecline(false)}
                              disabled={busy}
                            >
                              Keep enquiry open
                            </Button>
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="subtle">
                        This request is {r.status.toLowerCase()}. Its history
                        stays available, and no further status changes are
                        allowed.
                      </p>
                    )}
                  </section>
                )}
                <section className="panel">
                  <div className="section-title">
                    <h2>Contact details</h2>
                    <UserRound size={18} />
                  </div>
                  <dl className="contact-list">
                    <dt>Name</dt>
                    <dd>{r.contactName}</dd>
                    <dt>Email</dt>
                    <dd>{r.contactEmail}</dd>
                    <dt>Phone</dt>
                    <dd>{r.contactPhone}</dd>
                  </dl>
                  <p className="subtle small">
                    Sample contact details. No email or phone messages are sent
                    by this app.
                  </p>
                </section>
                <section className="panel service-snapshot">
                  <div className="eyebrow">SERVICE AT SUBMISSION</div>
                  <h3>{r.serviceName}</h3>
                  <p>{r.serviceDescription}</p>
                  <strong>{r.servicePrice}</strong>
                  <p className="subtle small">
                    Indicative price. This snapshot is kept even if the
                    catalogue changes.
                  </p>
                </section>
                <Button
                  className="text-link"
                  onClick={reload}
                  disabled={loading}
                >
                  <RefreshCw size={15} /> Reload latest details
                </Button>
              </aside>
            </div>
          </>
        )
      )}
    </>
  );
}
