import {
  useLayoutEffect,
  useMemo,
  useState,
  type ReactNode,
  type SetStateAction,
} from "react";
import {
  ArrowRight,
  House,
  LoaderCircle,
  AlertCircle,
  CheckCircle2,
  Wrench,
  Sprout,
  PaintRoller,
  Sparkles,
} from "lucide-react";
import { Link } from "react-router-dom";
import type { Status, Service } from "../shared/contracts";
export const ServiceIcon = ({
  category,
  size = 24,
}: {
  category: Service["category"];
  size?: number;
}) => {
  const Icon = {
    repair: Wrench,
    garden: Sprout,
    painting: PaintRoller,
    cleaning: Sparkles,
  }[category];
  return <Icon size={size} aria-hidden="true" />;
};
export function Brand() {
  return (
    <Link className="brand" to="/" aria-label="Hearth and Home, home">
      <span className="brand-icon">
        <House size={23} />
      </span>
      <span>
        hearth<span className="amp">&</span>home
        <small>LOCAL CARE. EVERYDAY COMFORT.</small>
      </span>
    </Link>
  );
}
export function Button({
  children,
  busy = false,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { busy?: boolean }) {
  return (
    <button {...props} disabled={props.disabled || busy}>
      {busy && <LoaderCircle className="spin" size={17} aria-hidden="true" />}
      {children}
    </button>
  );
}
export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={"status status-" + status.toLowerCase()}>
      <span />
      {status}
    </span>
  );
}
export function Notice({
  children,
  error = false,
}: {
  children: ReactNode;
  error?: boolean;
}) {
  return (
    <div
      className={"notice " + (error ? "error" : "success")}
      role={error ? "alert" : "status"}
    >
      {error ? <AlertCircle size={19} /> : <CheckCircle2 size={19} />}
      <span>{children}</span>
    </div>
  );
}
export function Loading() {
  return (
    <div className="loading" role="status">
      <LoaderCircle className="spin" /> Loading your workspace…
    </div>
  );
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <House size={34} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Field({
  label,
  name,
  error,
  hint,
  children,
}: {
  label: string;
  name: string;
  error?: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      {children}
      {hint && <small id={name + "-hint"}>{hint}</small>}
      {error && (
        <small className="field-error" id={name + "-error"}>
          {error}
        </small>
      )}
    </div>
  );
}
export function useResource<T>(
  load: () => Promise<T>,
  dependencies: unknown[] = [],
) {
  // One token per resource/owner. Render only data tagged with that token;
  // dependency changes never display the preceding owner's snapshot.
  const identity = useMemo(
    () => ({ active: false, generation: 0 }),
    dependencies,
  );
  const [state, setState] = useState({
    identity,
    data: null as T | null,
    error: "",
    loading: true,
  });
  async function reload() {
    if (!identity.active) return;
    const generation = ++identity.generation;
    setState((previous) => ({
      identity,
      data: previous.identity === identity ? previous.data : null,
      error: "",
      loading: true,
    }));
    try {
      const data = await load();
      if (identity.active && generation === identity.generation)
        setState({ identity, data, error: "", loading: false });
    } catch (e) {
      if (identity.active && generation === identity.generation)
        setState((previous) => ({
          identity,
          data: previous.identity === identity ? previous.data : null,
          error: (e as Error).message,
          loading: false,
        }));
    }
  }
  function setData(value: SetStateAction<T | null>) {
    if (!identity.active) return;
    // Applying an authoritative committed result supersedes every older read,
    // including its error/loading completion, not just its successful data.
    ++identity.generation;
    setState((previous) => ({
      identity,
      data:
        typeof value === "function"
          ? (value as (previous: T | null) => T | null)(
              previous.identity === identity ? previous.data : null,
            )
          : value,
      error: "",
      loading: false,
    }));
  }
  useLayoutEffect(() => {
    identity.active = true;
    void reload();
    return () => {
      identity.active = false;
      ++identity.generation;
    };
  }, [identity]);
  return {
    data: state.identity === identity ? state.data : null,
    error: state.identity === identity ? state.error : "",
    loading: state.identity === identity ? state.loading : true,
    setData,
    reload,
  };
}
export function PageIntro({
  eyebrow,
  title,
  children,
  action,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="page-intro">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{children}</p>
      </div>
      {action}
    </div>
  );
}
export function ArrowLink({
  to,
  children,
  className = "button",
}: {
  to: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Link to={to} className={className}>
      {children}
      <ArrowRight size={18} />
    </Link>
  );
}
export const dateLabel = (value: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value.length === 10 ? value + "T00:00:00Z" : value));
export const dateTime = (value: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
