import {
  useEffect,
  useState,
  createContext,
  useContext,
  type ReactNode,
} from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  NavLink,
  Navigate,
  useLocation,
} from "react-router-dom";
import {
  LayoutDashboard,
  ClipboardList,
  ArrowUpRight,
  LogOut,
  Settings2,
  House,
  Menu,
  X,
  ShieldCheck,
} from "lucide-react";
import { api, authClient } from "./api";
import { Brand, Button, Loading, Notice } from "./components";
import { Landing } from "./landing";
import { Login, RequestForm } from "./forms";
import { Dashboard } from "./dashboard";
import { Detail } from "./detail";
import { Catalogue } from "./catalogue";
import type { User } from "../shared/contracts";
import "./styles.css";
const SessionContext = createContext<{
  user: User | null;
  ready: boolean;
  setUser: (u: User | null) => void;
}>({ user: null, ready: false, setUser: () => {} });
function App() {
  const [user, setUser] = useState<User | null>(null),
    [ready, setReady] = useState(false),
    [error, setError] = useState("");
  async function load() {
    setError("");
    try {
      setUser(await api<User>("/me"));
    } catch (e) {
      if ((e as { status: number }).status !== 401)
        setError((e as Error).message);
    } finally {
      setReady(true);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  return (
    <SessionContext.Provider value={{ user, ready, setUser }}>
      <BrowserRouter>
        <RouteFocus />
        {error ? (
          <div className="container">
            <Notice error>
              {error} <Button onClick={load}>Retry sign-in check</Button>
            </Notice>
          </div>
        ) : (
          <Routes>
            <Route
              path="/"
              element={
                <PublicLayout>
                  <Landing />
                </PublicLayout>
              }
            />
            <Route
              path="/login"
              element={
                <PublicLayout>
                  <Login onLogin={setUser} />
                </PublicLayout>
              }
            />
            <Route
              path="/request"
              element={
                <Protected customer>
                  <PublicLayout>
                    <RequestForm user={user!} />
                  </PublicLayout>
                </Protected>
              }
            />
            <Route
              path="/dashboard"
              element={
                <Protected>
                  <Workspace>
                    <Dashboard user={user!} />
                  </Workspace>
                </Protected>
              }
            />
            <Route
              path="/requests/:id"
              element={
                <Protected>
                  <Workspace>
                    <Detail user={user!} />
                  </Workspace>
                </Protected>
              }
            />
            <Route
              path="/services"
              element={
                <Protected admin>
                  <Workspace>
                    <Catalogue user={user!} />
                  </Workspace>
                </Protected>
              }
            />
            <Route
              path="*"
              element={
                <PublicLayout>
                  <div className="container not-found">
                    <h1>That page isn’t here.</h1>
                    <p>
                      Return home or open your dashboard to find your requests.
                    </p>
                    <Link className="button" to="/">
                      Back home
                    </Link>
                  </div>
                </PublicLayout>
              }
            />
          </Routes>
        )}
      </BrowserRouter>
    </SessionContext.Provider>
  );
}
function RouteFocus() {
  const location = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
    setTimeout(() => {
      document.getElementById("main-content")?.focus({ preventScroll: true });
    }, 0);
  }, [location.pathname]);
  return null;
}
function Protected({
  children,
  admin = false,
  customer = false,
}: {
  children: ReactNode;
  admin?: boolean;
  customer?: boolean;
}) {
  const { user, ready } = useContext(SessionContext);
  if (!ready) return <Loading />;
  if (!user)
    return (
      <Navigate to={customer ? "/login?next=request" : "/login"} replace />
    );
  if (
    (admin && user.role !== "admin") ||
    (customer && user.role !== "customer")
  )
    return <Navigate to="/dashboard" replace />;
  return children;
}
function PublicLayout({ children }: { children: ReactNode }) {
  const { user } = useContext(SessionContext),
    [menu, setMenu] = useState(false);
  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="public-header container">
        <Brand />
        <button
          className="mobile-menu icon-button"
          aria-label={menu ? "Close navigation" : "Open navigation"}
          aria-expanded={menu}
          onClick={() => setMenu(!menu)}
        >
          {menu ? <X /> : <Menu />}
        </button>
        <nav className={menu ? "open" : ""} aria-label="Main navigation">
          <a href="/#services" onClick={() => setMenu(false)}>
            Our services
          </a>
          <a href="/#how-it-works" onClick={() => setMenu(false)}>
            How it works
          </a>
          <Link to={user ? "/dashboard" : "/login"}>
            {user ? "My dashboard" : "Sign in"} <ArrowUpRight size={15} />
          </Link>
          <Link className="button" to="/request">
            Request a service <ArrowUpRight size={16} />
          </Link>
        </nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        {children}
      </main>
      <Footer />
    </>
  );
}
function Footer() {
  return (
    <footer className="footer container">
      <div>
        <Brand />
        <p>Thoughtful help for the place you call home.</p>
      </div>
      <div className="portfolio-note">
        <span>SERVICEFLOW · A FICTIONAL BUSINESS DEMO</span>
        <p>
          Designed & developed as an{" "}
          <a
            href="https://www.aethdesign.com/"
            target="_blank"
            rel="noreferrer"
          >
            AethDesign portfolio demonstration <ArrowUpRight size={12} />
          </a>
          .<br />
          No real customers, client relationship or service bookings.
        </p>
      </div>
    </footer>
  );
}
function Workspace({ children }: { children: ReactNode }) {
  const { user, setUser } = useContext(SessionContext),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [menu, setMenu] = useState(false),
    location = useLocation();
  async function logout() {
    setBusy(true);
    setError("");
    try {
      const result = await authClient.signOut();
      if (result.error) throw new Error(result.error.message);
      sessionStorage.clear();
      setUser(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => setMenu(false), [location.pathname]);
  return (
    <div className="workspace">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className={"sidebar " + (menu ? "mobile-open" : "")}>
        <Brand />
        <div className="sidebar-label">
          {user?.role === "customer" ? "YOUR SPACE" : "TEAM WORKSPACE"}
        </div>
        <nav aria-label="Workspace navigation">
          <NavLink to="/dashboard">
            <LayoutDashboard size={19} /> Overview
          </NavLink>
          {user?.role === "customer" ? (
            <NavLink to="/request">
              <ClipboardList size={19} /> Request a service
            </NavLink>
          ) : (
            <a href="/dashboard#requests">
              <ClipboardList size={19} /> Requests
            </a>
          )}
          {user?.role === "admin" && (
            <NavLink to="/services">
              <Settings2 size={19} /> Service catalogue
            </NavLink>
          )}
          <Link to="/">
            <House size={19} /> View website <ArrowUpRight size={14} />
          </Link>
        </nav>
        <div className="sidebar-bottom">
          <div className="demo-marker">
            <ShieldCheck size={20} />
            <strong>Made for the demo.</strong>
            <p>
              Sample accounts. Real workflows.
              <br />A ServiceFlow portfolio project.
            </p>
          </div>
          <div className="user-card">
            <span className="avatar">
              {user?.name
                .split(" ")
                .map((n) => n[0])
                .join("")}
            </span>
            <span>
              <strong>{user?.name}</strong>
              <small>
                {user?.role === "admin"
                  ? "Administrator"
                  : user?.role === "provider"
                    ? "Service provider"
                    : "Customer account"}
              </small>
            </span>
          </div>
          <Button className="logout text-link" onClick={logout} busy={busy}>
            <LogOut size={17} /> Sign out
          </Button>
        </div>
      </aside>
      <div className="workspace-body">
        <header className="workspace-header">
          <div>
            <button
              className="mobile-menu icon-button"
              aria-label={
                menu
                  ? "Close workspace navigation"
                  : "Open workspace navigation"
              }
              aria-expanded={menu}
              onClick={() => setMenu(!menu)}
            >
              {menu ? <X /> : <Menu />}
            </button>
            <span>
              ServiceFlow <span className="breadcrumb-divider">/</span>{" "}
              {location.pathname === "/services"
                ? "Services"
                : location.pathname.startsWith("/requests/")
                  ? "Request detail"
                  : "Overview"}
            </span>
          </div>
          <span className="demo-pill">Portfolio demo</span>
        </header>
        <main className="workspace-content" id="main-content" tabIndex={-1}>
          {error && <Notice error>{error}</Notice>}
          {children}
        </main>
        <div className="workspace-footer">
          Hearth & Home is fictional.{" "}
          <span>ServiceFlow · An AethDesign portfolio demonstration</span>
        </div>
      </div>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
