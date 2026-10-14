import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Search,
  ArrowUpRight,
  Plus,
  Inbox,
  Clock3,
  CheckCircle2,
  SlidersHorizontal,
} from "lucide-react";
import { api } from "./api";
import {
  ArrowLink,
  Empty,
  Loading,
  Notice,
  PageIntro,
  StatusBadge,
  dateLabel,
  ServiceIcon,
  useResource,
} from "./components";
import {
  statuses,
  type ServiceRequest,
  type User,
  type Status,
} from "../shared/contracts";
export function Dashboard({ user }: { user: User }) {
  const { data, error, loading, reload } = useResource(
    () => api<ServiceRequest[]>("/requests"),
    [user.id],
  );
  const [query, setQuery] = useState(""),
    [filter, setFilter] = useState<Status | "">("");
  const staff = user.role !== "customer",
    requests = data || [],
    counts = Object.fromEntries(
      statuses.map((s) => [s, requests.filter((r) => r.status === s).length]),
    );
  const visible = requests.filter(
    (r) =>
      (!filter || r.status === filter) &&
      [r.serviceName, r.contactName, r.location, r.description, r.id]
        .join(" ")
        .toLowerCase()
        .includes(query.toLowerCase().trim()),
  );
  return (
    <>
      <PageIntro
        eyebrow={
          staff ? "HEARTH & HOME · TEAM WORKSPACE" : "YOUR HOME, TAKEN CARE OF"
        }
        title={
          staff
            ? "A clear view of every enquiry."
            : `Hello, ${user.name.split(" ")[0]}.`
        }
        action={
          !staff ? (
            <ArrowLink to="/request">
              <Plus size={17} /> New request
            </ArrowLink>
          ) : (
            <span className="workspace-tag">
              <span className="tiny-dot" />{" "}
              {user.role === "admin" ? "Administrator" : "Provider"} workspace
            </span>
          )
        }
      >
        {staff
          ? "Review the details, keep things moving, and give each home a little care."
          : "Your requests, their progress, and every little detail — all in one place."}
      </PageIntro>
      {error && (
        <Notice error>
          {error}{" "}
          <button onClick={reload} className="text-link">
            Try again
          </button>
        </Notice>
      )}
      {loading && !data ? (
        <Loading />
      ) : (
        <>
          <div className={staff ? "stat-grid" : "customer-stats"}>
            {staff ? (
              statuses.map((s, i) => (
                <button
                  key={s}
                  className={"stat-card " + (filter === s ? "selected" : "")}
                  onClick={() => setFilter(filter === s ? "" : s)}
                  aria-pressed={filter === s}
                >
                  <span>
                    {s}
                    <span className={"stat-dot dot-" + s.toLowerCase()} />
                  </span>
                  <strong>{counts[s]}</strong>
                  <small>
                    {
                      [
                        "Awaiting a first look",
                        "Details being reviewed",
                        "Ready for a decision",
                        "Agreed work",
                        "All taken care of",
                        "Closed enquiries",
                      ][i]
                    }
                  </small>
                </button>
              ))
            ) : (
              <>
                <div className="stat-card">
                  <span>
                    <Inbox size={18} /> Your enquiries
                  </span>
                  <strong>{requests.length}</strong>
                  <small>Everything you’ve requested</small>
                </div>
                <div className="stat-card">
                  <span>
                    <Clock3 size={18} /> In progress
                  </span>
                  <strong>
                    {
                      requests.filter(
                        (r) => !["Completed", "Declined"].includes(r.status),
                      ).length
                    }
                  </strong>
                  <small>From enquiry to booking</small>
                </div>
                <div className="stat-card">
                  <span>
                    <CheckCircle2 size={18} /> Completed
                  </span>
                  <strong>{counts.Completed}</strong>
                  <small>A few things off your list</small>
                </div>
              </>
            )}
          </div>
          {staff && requests.length > 0 && (
            <div className="recent-section">
              <div className="section-title">
                <h2>Recent enquiries</h2>
                <span className="subtle">Latest requests</span>
              </div>
              <div className="recent-grid">
                {requests.slice(0, 3).map((r) => (
                  <Link
                    className="panel recent-card"
                    to={"/requests/" + r.id}
                    key={r.id}
                  >
                    <div>
                      <StatusBadge status={r.status} />
                      <ArrowUpRight size={18} />
                    </div>
                    <h3>{r.serviceName}</h3>
                    <p>
                      {r.contactName} <span>·</span> {r.location}
                    </p>
                    <small>Submitted {dateLabel(r.createdAt)}</small>
                  </Link>
                ))}
              </div>
            </div>
          )}
          <section id="requests" className="requests-section">
            <div className="section-title">
              <h2>{staff ? "All requests" : "Your requests"}</h2>
              <span className="subtle">
                {visible.length}{" "}
                {visible.length === 1 ? "enquiry" : "enquiries"}
              </span>
            </div>
            <div className="filter-bar">
              <div className="search-field">
                <Search size={18} />
                <label className="sr-only" htmlFor="request-search">
                  Search requests
                </label>
                <input
                  id="request-search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={
                    staff
                      ? "Search name, service or postcode…"
                      : "Search your requests…"
                  }
                />
              </div>
              <div className="status-filter">
                <SlidersHorizontal size={17} />
                <label className="sr-only" htmlFor="status-filter">
                  Filter by status
                </label>
                <select
                  id="status-filter"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value as Status | "")}
                >
                  <option value="">All statuses</option>
                  {statuses.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>
            {visible.length === 0 ? (
              <Empty
                title={
                  requests.length
                    ? "No matching enquiries"
                    : "A calmer home starts with a request."
                }
              >
                {requests.length ? (
                  <button
                    className="text-link"
                    onClick={() => {
                      setQuery("");
                      setFilter("");
                    }}
                  >
                    Clear search and filters
                  </button>
                ) : (
                  <ArrowLink to="/request">Request a service</ArrowLink>
                )}
              </Empty>
            ) : staff ? (
              <div className="table-wrap panel">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Service & customer</th>
                      <th scope="col">Location</th>
                      <th scope="col">Preferred date</th>
                      <th scope="col">Status</th>
                      <th scope="col">
                        <span className="sr-only">Open request</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((r) => (
                      <tr key={r.id}>
                        <td>
                          <Link
                            className="table-title"
                            to={"/requests/" + r.id}
                          >
                            {r.serviceName}
                          </Link>
                          <small>{r.contactName}</small>
                        </td>
                        <td>{r.location}</td>
                        <td>
                          {dateLabel(r.preferredFrom)}
                          {r.preferredTo && (
                            <small>to {dateLabel(r.preferredTo)}</small>
                          )}
                        </td>
                        <td>
                          <StatusBadge status={r.status} />
                        </td>
                        <td>
                          <Link
                            className="icon-link"
                            aria-label={
                              "Open " + r.serviceName + " for " + r.contactName
                            }
                            to={"/requests/" + r.id}
                          >
                            <ArrowUpRight size={19} />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="customer-request-grid">
                {visible.map((r) => (
                  <Link
                    className="panel customer-request"
                    key={r.id}
                    to={"/requests/" + r.id}
                  >
                    <div className="request-card-top">
                      <span className="service-icon">
                        <ServiceIcon
                          category={
                            r.serviceName.toLowerCase().includes("garden")
                              ? "garden"
                              : r.serviceName.includes("Painting")
                                ? "painting"
                                : r.serviceName.includes("clean")
                                  ? "cleaning"
                                  : "repair"
                          }
                        />
                      </span>
                      <StatusBadge status={r.status} />
                    </div>
                    <h3>{r.serviceName}</h3>
                    <p>{r.description}</p>
                    <div className="request-meta">
                      <span>Preferred {dateLabel(r.preferredFrom)}</span>
                      <ArrowUpRight size={18} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>
          <div className="dashboard-note">
            <span className="tiny-dot" />
            <p>
              Preferred dates are requests, not confirmed appointments. Every
              status change is saved in the request’s history.
            </p>
          </div>
        </>
      )}
    </>
  );
}
