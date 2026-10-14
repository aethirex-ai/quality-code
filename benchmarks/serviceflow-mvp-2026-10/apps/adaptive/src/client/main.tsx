import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
  createContext,
  useContext,
} from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock3,
  ClipboardList,
  Flower2,
  Hammer,
  House,
  LayoutDashboard,
  Leaf,
  LogOut,
  MapPin,
  Paintbrush,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  Wrench,
  X,
  CircleHelp,
  LoaderCircle,
} from "lucide-react";
import type {
  Activity,
  Draft,
  RequestDetail,
  RequestInput,
  Role,
  Service,
  ServiceRequest,
  Status,
  User,
} from "../shared/contracts";
import { STATUSES } from "../shared/contracts";
import { api, ApiError, mutationOptions } from "./api";
import "./styles.css";

type AuthState = {
  user: User | null;
  loading: boolean;
  error: string;
  refresh: () => Promise<void>;
  notify: (s: string) => void;
};
const AuthContext = createContext<AuthState>(null!);
const useAuth = () => useContext(AuthContext);
const statusClass = (status: Status) => status.toLowerCase();
const date = (value: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value.length === 10 ? value + "T12:00:00" : value));
const errorText = (e: unknown) =>
  e instanceof Error ? e.message : "Please try again.";
const icons = [Wrench, Hammer, Flower2, Paintbrush];
function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className="brand" aria-label="Hearth and Home home">
      <span className="brand-mark">
        <House size={22} />
      </span>
      <span>
        Hearth <i>&</i> Home
        {!compact && <small>LOCAL CARE. THOUGHTFULLY DONE.</small>}
      </span>
    </Link>
  );
}
function Badge({ status }: { status: Status }) {
  return (
    <span className={`badge ${statusClass(status)}`}>
      <span />
      {status}
    </span>
  );
}
function Loading() {
  return (
    <div className="loading" role="status">
      <LoaderCircle className="spin" size={22} /> Loading your workspace…
    </div>
  );
}
function ErrorBox({
  message,
  children,
}: {
  message: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="error-box" role="alert">
      {message}
      {children}
    </div>
  );
}
function Empty({
  title,
  text,
  children,
}: {
  title: string;
  text: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <ClipboardList size={32} />
      <h3>{title}</h3>
      <p>{text}</p>
      {children}
    </div>
  );
}
function App() {
  const [user, setUser] = useState<User | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [toast, setToast] = useState("");
  const refresh = useCallback(async () => {
    try {
      const data = await api<{ user: User | null }>("/me");
      setUser(data.user);
      setError("");
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void refresh();
  }, [refresh]);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(""), 6500);
    return () => clearTimeout(t);
  }, [toast]);
  return (
    <AuthContext.Provider
      value={{ user, loading, error, refresh, notify: setToast }}
    >
      <ScrollReset />
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <div className="demo-strip">
        <span className="demo-dot" /> SERVICEFLOW{" "}
        <span className="demo-divider">/</span> A fictional business. A real
        product demo.
        <Link to="/login">
          Explore the demo <ArrowUpRight size={12} />
        </Link>
      </div>
      {toast && (
        <div className="toast" role="status">
          <CheckCircle2 size={18} />
          {toast}
          <button
            aria-label="Dismiss notification"
            onClick={() => setToast("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
      <Routes>
        <Route
          path="/"
          element={
            <PublicShell>
              <Landing />
            </PublicShell>
          }
        />
        <Route
          path="/services"
          element={
            <PublicShell>
              <ServicesPage />
            </PublicShell>
          }
        />
        <Route
          path="/login"
          element={
            <PublicShell>
              <Login />
            </PublicShell>
          }
        />
        <Route
          path="/request"
          element={
            <Protected roles={["customer"]}>
              <Workspace>
                <RequestForm />
              </Workspace>
            </Protected>
          }
        />
        <Route
          path="/dashboard"
          element={
            <Protected>
              <Workspace>
                <Dashboard />
              </Workspace>
            </Protected>
          }
        />
        <Route
          path="/requests/:id"
          element={
            <Protected>
              <Workspace>
                <RequestPage />
              </Workspace>
            </Protected>
          }
        />
        <Route
          path="/catalogue"
          element={
            <Protected roles={["admin"]}>
              <Workspace>
                <Catalogue />
              </Workspace>
            </Protected>
          }
        />
        <Route
          path="*"
          element={
            <PublicShell>
              <div className="page-narrow">
                <h1>We couldn’t find that page.</h1>
                <p>Return home to explore services or open your dashboard.</p>
                <Link className="button" to="/">
                  Back home <ArrowRight size={16} />
                </Link>
              </div>
            </PublicShell>
          }
        />
      </Routes>
    </AuthContext.Provider>
  );
}
function ScrollReset() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}
function PublicShell({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  return (
    <>
      <header className="public-header">
        <Logo />
        <nav aria-label="Main navigation">
          <NavLink to="/services">Our services</NavLink>
          <Link
            to="/#how-it-works"
            onClick={() =>
              setTimeout(
                () =>
                  document
                    .getElementById("how-it-works")
                    ?.scrollIntoView({ behavior: "smooth" }),
                80,
              )
            }
          >
            How it works
          </Link>
          <Link className="nav-account" to={user ? "/dashboard" : "/login"}>
            {user ? "Dashboard" : "Sign in"}
          </Link>
          <Link className="button small" to="/request">
            Request a service <ArrowUpRight size={15} />
          </Link>
        </nav>
      </header>
      <main id="main">{children}</main>
      <Footer />
    </>
  );
}
function Footer() {
  return (
    <footer className="footer">
      <Logo compact />
      <p>Care for your home. Space for your life.</p>
      <div className="footer-meta">
        <span>Fictional Bristol service business · Sample data only</span>
        <span>
          ServiceFlow · A portfolio demonstration by{" "}
          <a
            href="https://www.aethdesign.com/"
            target="_blank"
            rel="noreferrer"
          >
            AethDesign <ArrowUpRight size={12} />
          </a>
        </span>
      </div>
    </footer>
  );
}
function HomeIllustration() {
  return (
    <svg
      className="home-art"
      viewBox="0 0 560 460"
      role="img"
      aria-label="Illustration of a welcoming home with a garden"
    >
      <defs>
        <pattern
          id="lines"
          width="20"
          height="20"
          patternUnits="userSpaceOnUse"
        >
          <path d="M0 20L20 0" stroke="#c6d4c1" strokeWidth=".6" />
        </pattern>
        <linearGradient id="wall" x2="0" y2="1">
          <stop stopColor="#efe9dc" />
          <stop offset="1" stopColor="#e2d9c7" />
        </linearGradient>
      </defs>
      <circle cx="288" cy="225" r="193" fill="#dce5d5" />
      <circle cx="288" cy="225" r="170" fill="url(#lines)" />
      <path d="M60 389H507" stroke="#b0bea7" strokeWidth="2" />
      <ellipse
        cx="287"
        cy="397"
        rx="193"
        ry="13"
        fill="#b4c5aa"
        opacity=".45"
      />
      <path d="M147 204L300 87L454 205V387H147Z" fill="url(#wall)" />
      <path
        d="M125 204L299 64L474 204L457 225L299 99L142 225Z"
        fill="#315c49"
      />
      <path d="M387 84H420V161L387 137Z" fill="#315c49" />
      <path
        d="M213 387V274Q213 231 257 231Q301 231 301 274V387Z"
        fill="#ab613d"
      />
      <path
        d="M225 387V278Q225 245 257 245Q289 245 289 278V387Z"
        fill="#b77c58"
      />
      <circle cx="278" cy="318" r="4" fill="#e3c69c" />
      <path
        d="M335 248H409V324H335Z"
        fill="#f9f5eb"
        stroke="#fffaf2"
        strokeWidth="10"
      />
      <path d="M341 253H402V318H341Z" fill="#789584" />
      <path d="M371 253V318M341 285H402" stroke="#f9f5eb" strokeWidth="5" />
      <path
        d="M270 164Q299 135 328 164V203H270Z"
        fill="#789584"
        stroke="#fffaf2"
        strokeWidth="7"
      />
      <path d="M299 148V203M270 177H328" stroke="#fffaf2" strokeWidth="5" />
      <path d="M326 327H420" stroke="#b5aa97" strokeWidth="6" />
      <path d="M198 387H316L338 416H176Z" fill="#f1eee1" />
      <path d="M204 394H309M193 404H322" stroke="#d8d3c1" strokeWidth="2" />
      <path d="M107 394V263" stroke="#6d7e50" strokeWidth="6" />
      <ellipse cx="108" cy="276" rx="43" ry="65" fill="#72875e" />
      <ellipse cx="92" cy="263" rx="26" ry="44" fill="#859873" />
      <path d="M457 389V294" stroke="#6d7e50" strokeWidth="5" />
      <ellipse cx="458" cy="300" rx="33" ry="52" fill="#8b9d74" />
      <path d="M122 387Q120 350 161 355Q178 325 207 355V387Z" fill="#74875c" />
      <path
        d="M342 389Q337 357 366 364Q382 336 398 363Q438 347 440 389Z"
        fill="#94a77d"
      />
      <path d="M403 387V357M384 384V351" stroke="#6d7e50" strokeWidth="2" />
      <circle cx="403" cy="356" r="6" fill="#d5a56c" />
      <circle cx="384" cy="350" r="6" fill="#bc805d" />
      <path
        d="M211 104L192 82M187 126L158 117M398 53L410 29"
        stroke="#b4c4ab"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="153" cy="192" r="4" fill="#d0a77e" />
      <circle cx="464" cy="111" r="5" fill="#d0a77e" />
    </svg>
  );
}
function Landing() {
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow">
            <span /> YOUR HOME, IN GOOD HANDS
          </div>
          <h1>
            A little help.
            <br />A happier <em>home.</em>
          </h1>
          <p>
            From the dripping tap to the garden that needs a little love. Tell
            us what needs doing, and we’ll take it from there.
          </p>
          <div className="hero-actions">
            <Link className="button" to="/request">
              Request a service <ArrowUpRight size={18} />
            </Link>
            <Link className="text-link" to="/services">
              Explore our services <ArrowRight size={16} />
            </Link>
          </div>
          <div className="hero-note">
            <MapPin size={16} />
            <span>
              Home services around Bristol{" "}
              <span className="muted">· Fictional demo</span>
            </span>
          </div>
        </div>
        <div className="hero-visual">
          <span className="art-label">
            <Leaf size={14} /> MORE TIME FOR WHAT MATTERS
          </span>
          <HomeIllustration />
          <div className="art-card">
            <span className="round-icon">
              <Check size={20} />
            </span>
            <div>
              <strong>Small jobs. Thoughtful care.</strong>
              <span>A simpler way to look after home.</span>
            </div>
          </div>
          <span className="art-caption">HOME IS A GOOD PLACE TO START.</span>
        </div>
      </section>
      <div className="promise-bar">
        <span>
          <ClipboardList />
          One simple request
        </span>
        <span>
          <CircleHelp />
          Clear next steps
        </span>
        <span>
          <ShieldCheck />
          You approve before booking
        </span>
      </div>
      <section className="section" id="services">
        <div className="section-heading">
          <div>
            <div className="eyebrow">A HELPING HAND, ROOM BY ROOM</div>
            <h2>What can we help with?</h2>
          </div>
          <Link className="text-link" to="/services">
            View all services <ArrowRight size={16} />
          </Link>
        </div>
        <ServiceCards limit={4} />
        <p className="section-note">
          Indicative prices only. We review every request before providing a
          quote.
        </p>
      </section>
      <section id="how-it-works" className="how-section">
        <div>
          <div className="eyebrow">LESS ADMIN. MORE LIVING.</div>
          <h2>
            A few details.
            <br />
            We’ll handle the next step.
          </h2>
          <p>
            A request is the start of a conversation, never a confirmed
            appointment.
          </p>
          <Link className="button" to="/request">
            Let’s get it sorted <ArrowUpRight size={16} />
          </Link>
        </div>
        <ol className="steps">
          <li>
            <span>01</span>
            <div>
              <h3>Tell us what needs doing</h3>
              <p>
                Pick a service, describe the job and share your preferred dates.
              </p>
            </div>
          </li>
          <li>
            <span>02</span>
            <div>
              <h3>We review your request</h3>
              <p>
                Your enquiry moves from review to a quote. Follow its progress
                in your dashboard.
              </p>
            </div>
          </li>
          <li>
            <span>03</span>
            <div>
              <h3>Agree a plan together</h3>
              <p>
                Booking comes after a quote. No automatic appointments or
                surprises.
              </p>
            </div>
          </li>
        </ol>
      </section>
      <section className="closing">
        <span className="round-icon">
          <House size={25} />
        </span>
        <h2>One less thing on your list.</h2>
        <p>Start with a small request. Make a little room for life.</p>
        <Link className="button" to="/request">
          Request a service <ArrowUpRight size={16} />
        </Link>
      </section>
    </>
  );
}
function ServiceCards({ limit }: { limit?: number }) {
  const [services, setServices] = useState<Service[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    api<{ services: Service[] }>("/services")
      .then((d) => setServices(d.services.filter((s) => s.active)))
      .catch((e) => setError(errorText(e)))
      .finally(() => setLoading(false));
  }, []);
  if (error) return <ErrorBox message={error} />;
  if (loading) return <Loading />;
  if (!services.length)
    return (
      <Empty
        title="The catalogue is being updated"
        text="Please come back soon to see available services."
      />
    );
  return (
    <div className="service-grid">
      {services.slice(0, limit).map((s, i) => {
        const Icon = icons[i % 4];
        return (
          <article className="service-card" key={s.id}>
            <span className={`service-icon tone-${i % 4}`}>
              <Icon size={25} />
            </span>
            <h3>{s.name}</h3>
            <p>{s.description}</p>
            <div className="service-bottom">
              <span>{s.price}</span>
              <Link
                to={`/request?service=${encodeURIComponent(s.id)}`}
                aria-label={`Request ${s.name}`}
              >
                <ArrowUpRight size={19} />
              </Link>
            </div>
          </article>
        );
      })}
    </div>
  );
}
function ServicesPage() {
  return (
    <div className="section services-page">
      <div className="eyebrow">A LITTLE CARE GOES A LONG WAY</div>
      <h1>Care for every corner.</h1>
      <p className="lead">
        Practical home and garden help from one local team. Choose a service to
        tell us what you have in mind.
      </p>
      <ServiceCards />
      <div className="info-note">
        <CircleHelp size={20} />
        <div>
          <strong>A price is a starting point, not a promise.</strong>
          <p>
            All prices are indicative. Your preferred date is a request, not a
            confirmed appointment. This fictional demo does not provide real
            services.
          </p>
        </div>
      </div>
    </div>
  );
}
function Protected({
  children,
  roles,
}: {
  children: React.ReactNode;
  roles?: Role[];
}) {
  const { user, loading, error, refresh } = useAuth();
  const location = useLocation();
  if (loading) return <Loading />;
  if (error)
    return (
      <div className="page-narrow">
        <ErrorBox message={error}>
          <button className="button" onClick={() => void refresh()}>
            Try again
          </button>
        </ErrorBox>
      </div>
    );
  if (!user)
    return (
      <Navigate
        replace
        to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}
      />
    );
  if (roles && !roles.includes(user.role))
    return (
      <PublicShell>
        <div className="page-narrow">
          <h1>This area isn’t available for your role.</h1>
          <Link className="button" to="/dashboard">
            Go to dashboard
          </Link>
        </div>
      </PublicShell>
    );
  return <>{children}</>;
}
function Login() {
  const { user, refresh, notify } = useAuth(),
    navigate = useNavigate(),
    [params] = useSearchParams();
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const requested = params.get("next");
  const destination =
    requested &&
    /^\/(request|dashboard|catalogue|requests)([/?]|$)/.test(requested)
      ? requested
      : "/dashboard";
  if (user) return <Navigate to={destination} replace />;
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(
        "/auth/sign-in/email",
        mutationOptions("POST", {
          email: email.trim().toLowerCase(),
          password,
        }),
      );
      await refresh();
      notify("You’re signed in. Welcome to ServiceFlow.");
      navigate(destination, { replace: true });
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-layout">
      <section className="login-story">
        <div className="eyebrow">A LITTLE LESS TO WORRY ABOUT</div>
        <h1>
          Your home.
          <br />
          Your requests.
          <br />
          <em>All in one place.</em>
        </h1>
        <p>
          Keep up with every enquiry, from the first hello to the finishing
          touches.
        </p>
        <div className="login-art">
          <HomeIllustration />
        </div>
      </section>
      <section className="login-panel">
        <span className="round-icon">
          <House size={23} />
        </span>
        <h2>Welcome back</h2>
        <p>Sign in to your ServiceFlow workspace.</p>
        <form onSubmit={submit}>
          {error && <ErrorBox message={error} />}
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <button className="button full" disabled={busy}>
            {busy ? (
              <>
                <LoaderCircle className="spin" size={17} />
                Signing in…
              </>
            ) : (
              <>
                Sign in <ArrowRight size={17} />
              </>
            )}
          </button>
        </form>
        <div className="demo-accounts">
          <div className="eyebrow">TRY THE DEMO</div>
          <p>Choose an account to fill in its synthetic credentials.</p>
          <div className="account-buttons">
            {[
              ["Customer", "customer"],
              ["Customer 2", "customer2"],
              ["Provider", "provider"],
              ["Admin", "admin"],
            ].map(([label, id]) => (
              <button
                type="button"
                key={id}
                onClick={() => {
                  setEmail(`${id}@serviceflow.demo`);
                  setPassword("DemoHome2026!");
                  setError("");
                }}
              >
                {label}
              </button>
            ))}
          </div>
          <small>
            All accounts use <code>DemoHome2026!</code>
            <br />
            No signup, real emails or real service bookings.
          </small>
        </div>
      </section>
    </div>
  );
}
function Workspace({ children }: { children: React.ReactNode }) {
  const { user, refresh, notify } = useAuth(),
    navigate = useNavigate(),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function logout() {
    setBusy(true);
    try {
      await api("/auth/sign-out", mutationOptions("POST", {}));
      await refresh();
      navigate("/");
      notify("You’ve signed out.");
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="workspace">
      <aside className="sidebar">
        <Logo compact />
        <div className="workspace-label">
          {user?.role === "customer" ? "YOUR HOME HUB" : "TEAM WORKSPACE"}
        </div>
        <nav aria-label="Workspace navigation">
          <NavLink to="/dashboard">
            <LayoutDashboard size={18} />
            {user?.role === "customer" ? "My requests" : "Overview"}
          </NavLink>
          {user?.role === "customer" && (
            <NavLink to="/request">
              <Plus size={18} />
              Request a service
            </NavLink>
          )}
          {user?.role === "admin" && (
            <NavLink to="/catalogue">
              <Wrench size={18} />
              Service catalogue
            </NavLink>
          )}
          <Link to="/services">
            <Leaf size={18} />
            Explore services <ArrowUpRight size={13} />
          </Link>
        </nav>
        <div className="sidebar-note">
          <span className="round-icon">
            <House size={18} />
          </span>
          <strong>
            Thoughtful care,
            <br />
            from start to finish.
          </strong>
          <p>Track the little things that make a home.</p>
          <small>Fictional business demo</small>
        </div>
        <div className="user-block">
          <span className="avatar">
            {user?.name
              .split(" ")
              .map((n) => n[0])
              .slice(0, 2)
              .join("")}
          </span>
          <div>
            <strong>{user?.name}</strong>
            <span>{user?.role}</span>
          </div>
          <button
            aria-label="Sign out"
            title="Sign out"
            onClick={() => void logout()}
            disabled={busy}
          >
            <LogOut size={18} />
          </button>
        </div>
        {error && <ErrorBox message={error} />}
      </aside>
      <div className="workspace-content">
        <header className="workspace-top">
          <span>
            <House size={14} /> Hearth & Home <ChevronRight size={13} />{" "}
            <strong>ServiceFlow</strong>
          </span>
          <span className="demo-pill">DEMO WORKSPACE</span>
        </header>
        <main id="main" className="workspace-main">
          {children}
        </main>
        <div className="workspace-footer">
          ServiceFlow · Fictional local business demo{" "}
          <span>Designed & built for the AethDesign portfolio</span>
        </div>
      </div>
    </div>
  );
}
function Dashboard() {
  const { user } = useAuth(),
    [requests, setRequests] = useState<ServiceRequest[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [search, setSearch] = useState(""),
    [status, setStatus] = useState("All");
  const load = () => {
    setLoading(true);
    api<{ requests: ServiceRequest[] }>("/requests")
      .then((d) => {
        setRequests(d.requests);
        setError("");
      })
      .catch((e) => setError(errorText(e)))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);
  const customer = user?.role === "customer";
  const sorted = [...requests].sort((a, b) =>
    b.createdAt.localeCompare(a.createdAt),
  );
  const filtered = sorted.filter(
    (r) =>
      (status === "All" || r.status === status) &&
      `${r.serviceName} ${r.description} ${r.contactName} ${r.location} ${r.id}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const active = requests.filter(
    (r) => !["Completed", "Declined"].includes(r.status),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            {customer
              ? "YOUR HOME, AT A GLANCE"
              : "HEARTH & HOME · ENQUIRY MANAGEMENT"}
          </div>
          <h1>
            {customer
              ? `Hello, ${user?.name.split(" ")[0]}.`
              : "A little order for the day."}
          </h1>
          <p>
            {customer
              ? "A clear view of what’s happening at home."
              : "Review enquiries, keep things moving and make the next step clear."}
          </p>
        </div>
        {customer ? (
          <Link className="button" to="/request">
            <Plus size={17} />
            New request
          </Link>
        ) : (
          <span className="role-tag">
            <Users size={15} />
            {user?.role === "admin" ? "Administrator" : "Service provider"}
          </span>
        )}
      </div>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox message={error}>
          <button className="text-link" onClick={load}>
            Try again
          </button>
        </ErrorBox>
      ) : (
        <>
          <div className={`stats-grid ${customer ? "customer-stats" : ""}`}>
            {(customer
              ? [
                  {
                    label: "Your requests",
                    count: requests.length,
                    icon: ClipboardList,
                  },
                  { label: "In progress", count: active.length, icon: Clock3 },
                  {
                    label: "Completed",
                    count: requests.filter((r) => r.status === "Completed")
                      .length,
                    icon: CheckCircle2,
                  },
                ]
              : STATUSES.map((s) => ({
                  label: s,
                  count: requests.filter((r) => r.status === s).length,
                  icon: s === "Completed" ? CheckCircle2 : ClipboardList,
                }))
            ).map(({ label, count, icon: Icon }) => (
              <div className="stat-card" key={label}>
                <span>
                  {label}
                  <Icon size={17} />
                </span>
                <strong>{count.toString().padStart(2, "0")}</strong>
                <small>
                  {label === "New"
                    ? "Ready for a first look"
                    : label === "Completed"
                      ? "All wrapped up"
                      : "Service enquiries"}
                </small>
              </div>
            ))}
          </div>
          {!customer && sorted.length > 0 && (
            <section className="recent-panel">
              <div className="panel-heading">
                <h2>Fresh in the inbox</h2>
                <span>Most recent enquiries</span>
              </div>
              <div className="recent-grid">
                {sorted.slice(0, 3).map((r) => (
                  <Link
                    className="recent-card"
                    key={r.id}
                    to={`/requests/${r.id}`}
                  >
                    <span className="recent-avatar">{r.contactName[0]}</span>
                    <div>
                      <strong>{r.contactName}</strong>
                      <span>
                        {r.serviceName} · {r.location}
                      </span>
                    </div>
                    <ArrowUpRight size={17} />
                  </Link>
                ))}
              </div>
            </section>
          )}
          <section className="request-panel">
            <div className="panel-heading">
              <div>
                <h2>{customer ? "Your service requests" : "All requests"}</h2>
                <p>
                  {customer
                    ? "Follow each enquiry from request to completion."
                    : "Every enquiry, with a clear next step."}
                </p>
              </div>
              <span className="count-label">{requests.length} total</span>
            </div>
            <div className="filters">
              <div className="search-field">
                <Search size={17} />
                <input
                  aria-label="Search requests"
                  placeholder={
                    customer
                      ? "Search your requests…"
                      : "Search name, service or location…"
                  }
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <select
                aria-label="Filter by status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="All">All statuses</option>
                {STATUSES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>
            {filtered.length ? (
              <div className="request-table">
                <div className="request-row table-head">
                  <span>
                    {customer ? "Service / Request" : "Customer / Service"}
                  </span>
                  <span>Location</span>
                  <span>Preferred date</span>
                  <span>Status</span>
                  <span />
                </div>
                {filtered.map((r) => (
                  <Link
                    className="request-row"
                    key={r.id}
                    to={`/requests/${r.id}`}
                  >
                    <span className="request-title">
                      <span className="table-icon">
                        <Wrench size={17} />
                      </span>
                      <span>
                        <strong>
                          {customer ? r.serviceName : r.contactName}
                        </strong>
                        <small>
                          {customer ? r.description : r.serviceName}
                        </small>
                      </span>
                    </span>
                    <span className="table-location">
                      <MapPin size={13} />
                      {r.location}
                    </span>
                    <span className="table-date">
                      {date(r.preferredDate)}
                      {r.preferredEndDate && (
                        <small>to {date(r.preferredEndDate)}</small>
                      )}
                    </span>
                    <Badge status={r.status} />
                    <ChevronRight size={17} />
                  </Link>
                ))}
              </div>
            ) : (
              <Empty
                title={
                  requests.length
                    ? "No matching requests"
                    : "A fresh start for your home"
                }
                text={
                  requests.length
                    ? "Try a different search or status filter."
                    : "When you submit a request, you can follow every next step here."
                }
              >
                {customer && !requests.length && (
                  <Link className="button" to="/request">
                    Request your first service <ArrowRight size={16} />
                  </Link>
                )}
              </Empty>
            )}
          </section>
          <div className="dashboard-note">
            <ShieldCheck size={17} />
            {customer
              ? "Your requests are visible only to you and the Hearth & Home team."
              : "Preferences are enquiries, not confirmed appointments. No message is sent automatically."}
          </div>
        </>
      )}
    </>
  );
}
const blankRequest = (user: User | null): RequestInput => ({
  serviceId: "",
  description: "",
  location: "",
  preferredDate: "",
  preferredEndDate: "",
  contactName: user?.name || "",
  contactEmail: user?.email || "",
  contactPhone: "",
});
function RequestForm() {
  const { user, notify } = useAuth(),
    navigate = useNavigate(),
    [params] = useSearchParams();
  const storageKey = `serviceflow-form-${user?.id}`;
  const [draft] = useState(() => {
    try {
      const stored = sessionStorage.getItem(storageKey);
      if (stored)
        return JSON.parse(stored) as { data: RequestInput; key: string };
    } catch {
      /* Unavailable storage does not prevent submission. */
    }
    return {
      data: { ...blankRequest(user), serviceId: params.get("service") || "" },
      key: crypto.randomUUID(),
    };
  });
  const [data, setData] = useState<RequestInput>(draft.data),
    token = useRef(draft.key),
    [services, setServices] = useState<Service[]>([]),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [fields, setFields] = useState<Record<string, string>>({});
  useEffect(() => {
    api<{ services: Service[] }>("/services")
      .then((d) => setServices(d.services.filter((s) => s.active)))
      .catch((e) => setError(errorText(e)))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    try {
      sessionStorage.setItem(
        storageKey,
        JSON.stringify({ data, key: token.current }),
      );
    } catch {
      /* Form continues without storage. */
    }
  }, [data, storageKey]);
  const change = (name: keyof RequestInput, value: string) => {
    setData((d) => ({ ...d, [name]: value }));
    setFields((f) => ({ ...f, [name]: "" }));
    setError("");
  };
  const selected = services.find((s) => s.id === data.serviceId);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const invalid: Record<string, string> = {};
    if (!selected) invalid.serviceId = "Choose an available service.";
    if (data.description.trim().length < 10)
      invalid.description = "Tell us a little more (at least 10 characters).";
    if (data.location.trim().length < 3)
      invalid.location = "Enter a postcode or area (at least 3 characters).";
    if (data.contactName.trim().length < 2)
      invalid.contactName = "Enter your full name.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.contactEmail.trim()))
      invalid.contactEmail = "Enter a valid email address.";
    if (data.contactPhone.replace(/\D/g, "").length < 7)
      invalid.contactPhone = "Enter a phone number with at least 7 digits.";
    if (
      !data.preferredDate ||
      data.preferredDate < new Date().toISOString().slice(0, 10)
    )
      invalid.preferredDate = "Choose today or a future date.";
    if (data.preferredEndDate && data.preferredEndDate < data.preferredDate)
      invalid.preferredEndDate =
        "Choose an end date on or after the start date.";
    if (Object.keys(invalid).length) {
      setFields(invalid);
      setError("Please check the highlighted fields.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await api<{ request: ServiceRequest }>(
        "/requests",
        mutationOptions("POST", data, token.current),
      );
      try {
        sessionStorage.removeItem(storageKey);
      } catch {
        /* Optional storage. */
      }
      notify("Request received. You can follow its progress here.");
      navigate(`/requests/${result.request.id}`, { replace: true });
    } catch (e) {
      setError(
        e instanceof ApiError &&
          e.status === 409 &&
          e.message.includes("operation key")
          ? "This request may already have been saved. Check your requests before creating another."
          : errorText(e),
      );
      if (e instanceof ApiError) setFields(e.body.fields || {});
    } finally {
      setBusy(false);
    }
  }
  function field(
    name: keyof RequestInput,
    label: string,
    options: {
      type?: string;
      placeholder?: string;
      max?: number;
      required?: boolean;
    } = {},
  ) {
    return (
      <div className="field">
        <label htmlFor={name}>
          {label}
          {options.required === false && <span>Optional</span>}
        </label>
        <input
          id={name}
          name={name}
          type={options.type || "text"}
          value={data[name] || ""}
          placeholder={options.placeholder}
          required={options.required !== false}
          maxLength={options.max}
          min={
            options.type === "date"
              ? new Date().toISOString().slice(0, 10)
              : undefined
          }
          autoComplete={
            name === "contactName"
              ? "name"
              : name === "contactEmail"
                ? "email"
                : name === "contactPhone"
                  ? "tel"
                  : name === "location"
                    ? "postal-code"
                    : undefined
          }
          aria-invalid={!!fields[name]}
          aria-describedby={fields[name] ? `${name}-error` : undefined}
          onChange={(e) => change(name, e.target.value)}
        />
        {fields[name] && (
          <small className="field-error" id={`${name}-error`}>
            {fields[name]}
          </small>
        )}
      </div>
    );
  }
  return (
    <>
      <Link className="back-link" to="/dashboard">
        ← Back to your requests
      </Link>
      <div className="page-heading">
        <div>
          <div className="eyebrow">LET’S MAKE HOME A LITTLE HAPPIER</div>
          <h1>What needs a helping hand?</h1>
          <p>
            Share a few details. The team will review your enquiry before any
            booking.
          </p>
        </div>
      </div>
      {loading ? (
        <Loading />
      ) : (
        <div className="form-layout">
          <form className="request-form" onSubmit={submit} noValidate>
            {error && <ErrorBox message={error} />}
            <section className="form-section">
              <div className="form-section-title">
                <span>01</span>
                <div>
                  <h2>The job at hand</h2>
                  <p>What would you like help with?</p>
                </div>
              </div>
              <div className="field">
                <label htmlFor="serviceId">Service</label>
                <select
                  id="serviceId"
                  value={data.serviceId}
                  onChange={(e) => change("serviceId", e.target.value)}
                  required
                  aria-invalid={!!fields.serviceId}
                  aria-describedby={
                    fields.serviceId ? "serviceId-error" : undefined
                  }
                >
                  <option value="">Choose a service</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} · {s.price}
                    </option>
                  ))}
                </select>
                {fields.serviceId && (
                  <small className="field-error" id="serviceId-error">
                    {fields.serviceId}
                  </small>
                )}
              </div>
              <div className="field">
                <label htmlFor="description">Tell us what needs doing</label>
                <textarea
                  id="description"
                  placeholder="For example: the kitchen tap has a slow leak, even when it’s turned off…"
                  rows={4}
                  value={data.description}
                  maxLength={2000}
                  minLength={10}
                  required
                  aria-invalid={!!fields.description}
                  aria-describedby={
                    fields.description
                      ? "description-error"
                      : "description-hint"
                  }
                  onChange={(e) => change("description", e.target.value)}
                />
                <small id="description-hint">
                  10–2,000 characters. Include useful job details; leave out
                  sensitive information.
                </small>
                {fields.description && (
                  <small className="field-error" id="description-error">
                    {fields.description}
                  </small>
                )}
              </div>
              {field("location", "Postcode or local area", {
                placeholder: "e.g. BS6 5AA, Bristol",
                max: 180,
              })}
            </section>
            <section className="form-section">
              <div className="form-section-title">
                <span>02</span>
                <div>
                  <h2>A date that suits you</h2>
                  <p>A preference, never a confirmed appointment.</p>
                </div>
              </div>
              <div className="two-fields">
                {field("preferredDate", "Preferred date", { type: "date" })}
                {field("preferredEndDate", "Until", {
                  type: "date",
                  required: false,
                })}
              </div>
            </section>
            <section className="form-section">
              <div className="form-section-title">
                <span>03</span>
                <div>
                  <h2>How to reach you</h2>
                  <p>Your details are shared only with the service team.</p>
                </div>
              </div>
              {field("contactName", "Contact name", {
                placeholder: "Your full name",
                max: 100,
              })}
              <div className="two-fields">
                {field("contactEmail", "Email address", {
                  type: "email",
                  max: 254,
                })}
                {field("contactPhone", "Phone number", {
                  type: "tel",
                  placeholder: "e.g. 07700 900123",
                  max: 40,
                })}
              </div>
            </section>
            <div className="form-submit">
              <span>
                <ShieldCheck size={16} /> No payment. No automatic booking.
              </span>
              <button className="button" disabled={busy || !services.length}>
                {busy ? (
                  <>
                    <LoaderCircle className="spin" size={16} />
                    Submitting…
                  </>
                ) : (
                  <>
                    Submit request <ArrowUpRight size={17} />
                  </>
                )}
              </button>
            </div>
          </form>
          <aside className="request-summary">
            <span className="round-icon">
              <ClipboardList size={23} />
            </span>
            <h3>A good start to getting it sorted.</h3>
            {selected ? (
              <div className="selected-service">
                <strong>{selected.name}</strong>
                <p>{selected.description}</p>
                <span>{selected.price}</span>
              </div>
            ) : (
              <p>Choose a service and tell us a little about the job.</p>
            )}
            <hr />
            <h4>What happens next?</h4>
            <ol>
              <li>
                Your enquiry starts as <strong>New</strong>.
              </li>
              <li>The team reviews your details.</li>
              <li>A quote comes before any booking.</li>
            </ol>
            <div className="info-note">
              <CircleHelp size={18} />
              <p>
                This is a portfolio demo. No real service, appointment or
                contact will take place.
              </p>
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
const nextStatuses: Record<Status, Status[]> = {
  New: ["Reviewing", "Declined"],
  Reviewing: ["Quoted", "Declined"],
  Quoted: ["Booked", "Declined"],
  Booked: ["Completed"],
  Completed: [],
  Declined: [],
};
function RequestPage() {
  const { id } = useParams(),
    { user, notify } = useAuth();
  const [detail, setDetail] = useState<RequestDetail | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [actionError, setActionError] = useState(""),
    [busy, setBusy] = useState(false),
    [next, setNext] = useState<Status | " ">(" "),
    [draft, setDraft] = useState<Draft | null>(null),
    [draftBusy, setDraftBusy] = useState(false),
    [draftError, setDraftError] = useState("");
  const load = useCallback(async () => {
    try {
      setDetail(await api<RequestDetail>(`/requests/${id}`));
      setError("");
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => {
    void load();
  }, [load]);
  const staff = user?.role !== "customer";
  async function update(e: React.FormEvent) {
    e.preventDefault();
    if (!detail || next === " ") return;
    setBusy(true);
    setActionError("");
    try {
      await api(
        `/requests/${id}/status`,
        mutationOptions(
          "PATCH",
          { status: next, version: detail.request.version },
          `${id}-${detail.request.version}-${next}`,
        ),
      );
      notify(`Request moved to ${next}.`);
      setNext(" ");
      await load();
    } catch (e) {
      setActionError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function generate() {
    setDraftBusy(true);
    setDraftError("");
    try {
      setDraft(
        await api<Draft>(`/requests/${id}/draft`, mutationOptions("POST", {})),
      );
    } catch (e) {
      setDraftError(errorText(e));
    } finally {
      setDraftBusy(false);
    }
  }
  if (loading) return <Loading />;
  if (error || !detail)
    return (
      <>
        <Link className="back-link" to="/dashboard">
          ← Back to requests
        </Link>
        <ErrorBox message={error || "Request unavailable."} />
      </>
    );
  const r = detail.request;
  const progress = ["New", "Reviewing", "Quoted", "Booked", "Completed"];
  return (
    <>
      <Link className="back-link" to="/dashboard">
        ← Back to {staff ? "all" : "your"} requests
      </Link>
      <div className="page-heading detail-heading">
        <div>
          <div className="eyebrow">
            REQUEST {r.id.slice(0, 8).toUpperCase()}
          </div>
          <h1>{r.serviceName}</h1>
          <p>
            Submitted {date(r.createdAt)} ·{" "}
            {staff ? r.contactName : "Your home enquiry"}
          </p>
        </div>
        <Badge status={r.status} />
      </div>
      <div
        className="progress-tracker"
        aria-label={`Current request status: ${r.status}`}
      >
        {r.status === "Declined" ? (
          <div className="declined-progress">
            <CircleHelp size={18} />
            <strong>This enquiry has been declined.</strong>
            <span>No appointment has been booked.</span>
          </div>
        ) : (
          progress.map((s, i) => (
            <div
              key={s}
              className={i <= progress.indexOf(r.status) ? "reached" : ""}
            >
              <span>
                {i < progress.indexOf(r.status) ? <Check size={14} /> : i + 1}
              </span>
              <strong>{s}</strong>
            </div>
          ))
        )}
      </div>
      <div className="detail-layout">
        <div className="detail-primary">
          <section className="detail-card">
            <div className="panel-heading">
              <h2>The request</h2>
              <span className="tiny-label">SUPPLIED BY CUSTOMER</span>
            </div>
            <div className="detail-description">
              <div className="eyebrow">WHAT NEEDS DOING</div>
              <p>{r.description}</p>
            </div>
            <dl className="detail-grid">
              <div>
                <dt>
                  <MapPin size={15} />
                  Location
                </dt>
                <dd>{r.location}</dd>
              </div>
              <div>
                <dt>
                  <Clock3 size={15} />
                  Date preference
                </dt>
                <dd>
                  {date(r.preferredDate)}
                  {r.preferredEndDate && ` – ${date(r.preferredEndDate)}`}
                  <small>Not a confirmed appointment</small>
                </dd>
              </div>
              <div>
                <dt>
                  <Wrench size={15} />
                  Selected service
                </dt>
                <dd>
                  {r.serviceName}
                  <small>{r.servicePrice} · Indicative price</small>
                </dd>
              </div>
              <div>
                <dt>
                  <Users size={15} />
                  Contact
                </dt>
                <dd>
                  {r.contactName}
                  <small>{r.contactEmail}</small>
                  <small>{r.contactPhone}</small>
                </dd>
              </div>
            </dl>
          </section>
          <section className="detail-card history-card">
            <div className="panel-heading">
              <h2>Request history</h2>
              <span className="count-label">
                {detail.history.length} events
              </span>
            </div>
            <ol className="timeline">
              {detail.history.map((h: Activity) => (
                <li key={h.id}>
                  <span className="timeline-dot">
                    <Check size={11} />
                  </span>
                  <div>
                    <strong>{h.action}</strong>
                    <span>
                      {h.actorName} <span className="dot-separator">·</span>{" "}
                      {date(h.createdAt)} at{" "}
                      {new Date(h.createdAt).toLocaleTimeString("en-GB", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </div>
        <aside className="detail-side">
          {staff ? (
            <>
              <section className="detail-card status-action">
                <div className="eyebrow">KEEP THINGS MOVING</div>
                <h2>The next step</h2>
                <p>Changes are saved with your name in the request history.</p>
                {actionError && <ErrorBox message={actionError} />}
                <form onSubmit={update}>
                  {nextStatuses[r.status].length ? (
                    <>
                      <label htmlFor="next-status">Update status</label>
                      <select
                        id="next-status"
                        value={next}
                        onChange={(e) => setNext(e.target.value as Status)}
                        required
                      >
                        <option value=" ">Choose next status</option>
                        {nextStatuses[r.status].map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                      {next === "Declined" && (
                        <p className="decline-note">
                          Declining ends this enquiry. This action cannot be
                          reversed.
                        </p>
                      )}
                      <button
                        className="button full"
                        disabled={busy || next === " "}
                      >
                        {busy
                          ? "Saving…"
                          : next === "Declined"
                            ? "Decline request"
                            : "Save status"}
                        <ArrowRight size={16} />
                      </button>
                    </>
                  ) : (
                    <div className="terminal-note">
                      <CheckCircle2 size={19} />
                      <span>
                        This request is {r.status.toLowerCase()}. Its history is
                        preserved.
                      </span>
                    </div>
                  )}
                </form>
                {actionError && (
                  <button
                    className="text-link refresh-link"
                    onClick={() => {
                      void load();
                      setNext(" ");
                      setActionError("");
                    }}
                  >
                    Refresh request
                  </button>
                )}
              </section>
              <section className="detail-card draft-card">
                <span className="round-icon">
                  <Sparkles size={21} />
                </span>
                <h2>A thoughtful first reply</h2>
                <p>
                  Create a starting point from the job details, then edit it in
                  your own words.
                </p>
                {draftError && <ErrorBox message={draftError} />}
                <button
                  className="button secondary full"
                  disabled={draftBusy}
                  onClick={() => void generate()}
                >
                  {draftBusy ? (
                    <>
                      <LoaderCircle size={16} className="spin" />
                      Drafting…
                    </>
                  ) : (
                    <>
                      <Sparkles size={16} />
                      {draft ? "Regenerate draft" : "Draft reply"}
                    </>
                  )}
                </button>
                {draft && (
                  <div className="generated-draft">
                    <span className="draft-label">
                      {draft.source === "deterministic-demo"
                        ? "DETERMINISTIC DEMO-GENERATED"
                        : "AI-GENERATED"}{" "}
                      · REVIEW REQUIRED
                    </span>
                    <label htmlFor="draft-text">Edit your draft</label>
                    <textarea
                      id="draft-text"
                      rows={10}
                      value={draft.text}
                      maxLength={10000}
                      onChange={(e) =>
                        setDraft({ ...draft, text: e.target.value })
                      }
                    />
                    <div className="info-note">
                      <ShieldCheck size={17} />
                      <p>
                        Review before using. This draft has not been sent.
                        Drafting does not change the request status.
                      </p>
                    </div>
                  </div>
                )}
                <small>No message is sent from this demo.</small>
              </section>
            </>
          ) : (
            <section className="detail-card customer-note">
              <span className="round-icon">
                <Leaf size={22} />
              </span>
              <h2>You’re all caught up.</h2>
              <p>
                Each update will appear here. Check back to follow your
                enquiry’s progress.
              </p>
              <div className="info-note">
                <Clock3 size={18} />
                <p>
                  Preferred dates are requests. A booking comes only after a
                  quote.
                </p>
              </div>
            </section>
          )}
        </aside>
      </div>
    </>
  );
}
function Catalogue() {
  const { notify } = useAuth(),
    [services, setServices] = useState<Service[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [editing, setEditing] = useState<Service | null | "new">(null),
    [busy, setBusy] = useState(false),
    [actionError, setActionError] = useState(""),
    [confirmDelete, setConfirmDelete] = useState<Service | null>(null);
  const [name, setName] = useState(""),
    [description, setDescription] = useState(""),
    [price, setPrice] = useState(""),
    [active, setActive] = useState(true),
    [fields, setFields] = useState<Record<string, string>>({});
  const token = useRef(crypto.randomUUID());
  const load = useCallback(async () => {
    try {
      const d = await api<{ services: Service[] }>("/services");
      setServices(d.services);
      setError("");
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  const dialogReturnFocus = useRef<HTMLElement | null>(null);
  const dialogOpen = Boolean(editing || confirmDelete);
  useEffect(() => {
    if (!dialogOpen) return;
    document.body.classList.add("dialog-open");
    return () => {
      document.body.classList.remove("dialog-open");
      if (dialogReturnFocus.current?.isConnected)
        dialogReturnFocus.current.focus();
    };
  }, [dialogOpen]);
  function edit(s: Service | "new") {
    dialogReturnFocus.current = document.activeElement as HTMLElement;
    setEditing(s);
    setName(s === "new" ? "" : s.name);
    setDescription(s === "new" ? "" : s.description);
    setPrice(s === "new" ? "" : s.price);
    setActive(s === "new" ? true : s.active);
    setFields({});
    setActionError("");
    token.current = crypto.randomUUID();
    setTimeout(() => document.getElementById("service-name")?.focus(), 60);
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    setBusy(true);
    setActionError("");
    try {
      const data = {
        name,
        description,
        price,
        active,
        ...(editing === "new" ? {} : { version: editing.version }),
      };
      await api(
        editing === "new" ? "/services" : `/services/${editing.id}`,
        mutationOptions(
          editing === "new" ? "POST" : "PATCH",
          data,
          token.current,
        ),
      );
      notify(
        editing === "new"
          ? "Service created."
          : "Service updated. Historical request details are preserved.",
      );
      setEditing(null);
      await load();
    } catch (e) {
      setActionError(errorText(e));
      if (e instanceof ApiError) setFields(e.body.fields || {});
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    if (!confirmDelete) return;
    setBusy(true);
    setActionError("");
    try {
      await api(
        `/services/${confirmDelete.id}?version=${confirmDelete.version}`,
        mutationOptions(
          "DELETE",
          {},
          `delete-${confirmDelete.id}-${confirmDelete.version}`,
        ),
      );
      notify("Unreferenced service deleted.");
      setConfirmDelete(null);
      await load();
    } catch (e) {
      setActionError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">ADMINISTRATION</div>
          <h1>A useful service for every job.</h1>
          <p>
            Manage the catalogue. Existing requests keep their original service
            details.
          </p>
        </div>
        <button className="button" onClick={() => edit("new")}>
          <Plus size={17} />
          Add service
        </button>
      </div>
      <div className="info-note catalogue-info">
        <ShieldCheck size={20} />
        <div>
          <strong>Keep the history. Control what’s available.</strong>
          <p>
            Inactive services cannot receive new requests. A service with
            request history can be deactivated, but cannot be deleted.
          </p>
        </div>
      </div>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox message={error} />
      ) : (
        <div className="catalogue-grid">
          {services.map((s, i) => {
            const Icon = icons[i % 4];
            return (
              <article
                className={`service-card catalogue-card ${!s.active ? "inactive-card" : ""}`}
                key={s.id}
              >
                <div className="catalogue-card-top">
                  <span className={`service-icon tone-${i % 4}`}>
                    <Icon size={24} />
                  </span>
                  <span className={`availability ${s.active ? "active" : ""}`}>
                    {s.active ? "Active" : "Inactive"}
                  </span>
                </div>
                <h3>{s.name}</h3>
                <p>{s.description}</p>
                <strong className="catalogue-price">{s.price}</strong>
                <div className="catalogue-actions">
                  <button
                    className="button secondary small"
                    onClick={() => edit(s)}
                  >
                    Edit service <ArrowUpRight size={14} />
                  </button>
                  <button
                    className="delete-button"
                    onClick={() => {
                      dialogReturnFocus.current =
                        document.activeElement as HTMLElement;
                      setConfirmDelete(s);
                      setActionError("");
                    }}
                  >
                    Delete
                  </button>
                </div>
              </article>
            );
          })}
          {!services.length && (
            <Empty
              title="No services yet"
              text="Add a service to make it available for new enquiries."
            />
          )}
        </div>
      )}
      {editing && (
        <div className="modal-backdrop">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
            className="modal"
            onKeyDown={(e) => {
              if (e.key === "Escape" && !busy) setEditing(null);
              if (e.key === "Tab") {
                const focusable = Array.from(
                  e.currentTarget.querySelectorAll<HTMLElement>(
                    "button:not([disabled]),input,textarea,select",
                  ),
                );
                const first = focusable[0],
                  last = focusable[focusable.length - 1];
                if (e.shiftKey && document.activeElement === first) {
                  e.preventDefault();
                  last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                  e.preventDefault();
                  first.focus();
                }
              }
            }}
          >
            <div className="modal-heading">
              <h2 id="modal-title">
                {editing === "new" ? "Add a service" : "Edit service"}
              </h2>
              <button
                aria-label="Close editor"
                disabled={busy}
                onClick={() => setEditing(null)}
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={save}>
              {actionError && <ErrorBox message={actionError} />}
              <label htmlFor="service-name">Service name</label>
              <input
                id="service-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                minLength={3}
                maxLength={100}
                aria-invalid={!!fields.name}
                aria-describedby={
                  fields.name ? "service-name-error" : undefined
                }
              />
              {fields.name && (
                <small id="service-name-error" className="field-error">
                  {fields.name}
                </small>
              )}
              <label htmlFor="service-description">Description</label>
              <textarea
                id="service-description"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
                minLength={10}
                maxLength={700}
                aria-invalid={!!fields.description}
                aria-describedby={
                  fields.description ? "service-description-error" : undefined
                }
              />
              {fields.description && (
                <small id="service-description-error" className="field-error">
                  {fields.description}
                </small>
              )}
              <label htmlFor="service-price">
                Indicative price or quote label
              </label>
              <input
                id="service-price"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="e.g. From £65 or Request a quote"
                required
                minLength={2}
                maxLength={100}
                aria-invalid={!!fields.price}
                aria-describedby={
                  fields.price ? "service-price-error" : undefined
                }
              />
              {fields.price && (
                <small id="service-price-error" className="field-error">
                  {fields.price}
                </small>
              )}
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={active}
                  onChange={(e) => setActive(e.target.checked)}
                />
                Active — available for new requests
              </label>
              <div className="modal-actions">
                <button
                  type="button"
                  className="button secondary"
                  disabled={busy}
                  onClick={() => setEditing(null)}
                >
                  Cancel
                </button>
                <button className="button" disabled={busy}>
                  {busy ? "Saving…" : "Save service"}
                </button>
              </div>
              {actionError && (
                <button
                  type="button"
                  className="text-link"
                  onClick={async () => {
                    await load();
                    setEditing(null);
                  }}
                >
                  Close and refresh catalogue
                </button>
              )}
            </form>
          </section>
        </div>
      )}
      {confirmDelete && (
        <div className="modal-backdrop">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-title"
            className="modal"
            onKeyDown={(e) => {
              if (e.key === "Escape" && !busy) setConfirmDelete(null);
              if (e.key === "Tab") {
                const els = Array.from(
                  e.currentTarget.querySelectorAll<HTMLElement>(
                    "button:not([disabled])",
                  ),
                );
                if (e.shiftKey && document.activeElement === els[0]) {
                  e.preventDefault();
                  els[els.length - 1].focus();
                } else if (
                  !e.shiftKey &&
                  document.activeElement === els[els.length - 1]
                ) {
                  e.preventDefault();
                  els[0].focus();
                }
              }
            }}
          >
            <h2 id="delete-title">Delete {confirmDelete.name}?</h2>
            <p>
              Only services without request history can be deleted. To keep a
              referenced service’s history, edit it and turn off Active.
            </p>
            {actionError && <ErrorBox message={actionError} />}
            <div className="modal-actions">
              <button
                autoFocus
                className="button secondary"
                disabled={busy}
                onClick={() => setConfirmDelete(null)}
              >
                Cancel
              </button>
              <button
                className="button danger"
                disabled={busy}
                onClick={() => void remove()}
              >
                {busy ? "Deleting…" : "Delete service"}
              </button>
            </div>
          </section>
        </div>
      )}
    </>
  );
}
createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>,
);
