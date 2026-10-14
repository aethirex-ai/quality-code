import { Link } from "react-router-dom";
import {
  ArrowRight,
  MapPin,
  Check,
  ClipboardList,
  MessageSquare,
  HeartHandshake,
} from "lucide-react";
import { api } from "./api";
import {
  ArrowLink,
  ServiceIcon,
  useResource,
  Notice,
  Loading,
} from "./components";
import type { Service } from "../shared/contracts";
function HomeIllustration() {
  return (
    <svg
      className="home-art"
      viewBox="0 0 620 480"
      role="img"
      aria-labelledby="home-art-title"
    >
      <title id="home-art-title">
        Illustration of a welcoming home with a cared-for garden
      </title>
      <defs>
        <pattern
          id="lines"
          width="28"
          height="28"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M 0 28 L 28 0"
            stroke="#bbc5ac"
            strokeWidth=".7"
            opacity=".35"
          />
        </pattern>
      </defs>
      <rect width="620" height="480" rx="24" fill="#e5e8dc" />
      <rect width="620" height="480" rx="24" fill="url(#lines)" />
      <circle cx="467" cy="102" r="42" fill="#dfbb78" />
      <path d="M0 350 Q160 280 330 343 T620 325 V480 H0Z" fill="#c1cdb3" />
      <path
        d="M96 420 Q150 370 190 330"
        fill="none"
        stroke="#98ae8f"
        strokeWidth="65"
      />
      <rect x="204" y="179" width="251" height="209" fill="#f9f2e1" />
      <path d="M161 188 L319 70 L486 188Z" fill="#426354" />
      <path
        d="M181 181 L319 83 L464 181"
        fill="none"
        stroke="#658174"
        strokeWidth="6"
      />
      <rect x="405" y="96" width="27" height="55" fill="#426354" />
      <path d="M196 192 H465" stroke="#263f35" strokeWidth="8" />
      <rect x="289" y="265" width="62" height="123" rx="30" fill="#b77750" />
      <rect x="302" y="278" width="36" height="52" rx="18" fill="#dec8a5" />
      <circle cx="337" cy="350" r="3" fill="#f9f2e1" />
      <g fill="#a6c3bb" stroke="#446553" strokeWidth="5">
        <rect x="226" y="225" width="40" height="58" rx="2" />
        <rect x="377" y="225" width="40" height="58" rx="2" />
      </g>
      <g stroke="#f7f1de" strokeWidth="3">
        <path d="M246 225V283M226 251H266M397 225V283M377 251H417" />
      </g>
      <rect x="218" y="283" width="56" height="10" rx="2" fill="#b77750" />
      <rect x="368" y="283" width="56" height="10" rx="2" fill="#b77750" />
      <g fill="#57744b">
        <ellipse cx="231" cy="279" rx="13" ry="7" />
        <ellipse cx="256" cy="279" rx="13" ry="7" />
        <ellipse cx="382" cy="279" rx="13" ry="7" />
        <ellipse cx="409" cy="279" rx="13" ry="7" />
      </g>
      <path d="M290 393 L350 393 L393 480 H245Z" fill="#eddfc5" />
      <rect x="479" y="272" width="10" height="130" fill="#81654b" />
      <g fill="#6c8a5a">
        <circle cx="484" cy="240" r="46" />
        <circle cx="459" cy="275" r="35" />
        <circle cx="511" cy="276" r="34" />
      </g>
      <g fill="#8aa275">
        <circle cx="137" cy="352" r="26" />
        <circle cx="166" cy="357" r="30" />
        <circle cx="189" cy="363" r="20" />
      </g>
      <g stroke="#fbf6e8" strokeWidth="8">
        <path d="M68 378V431M104 378V431M140 385V431M69 395H157M69 416H150" />
      </g>
      <g fill="#d9b971">
        <circle cx="516" cy="405" r="5" />
        <circle cx="548" cy="424" r="5" />
        <circle cx="450" cy="429" r="5" />
      </g>
      <path
        d="M432 389 H464"
        stroke="#426354"
        strokeWidth="6"
        strokeLinecap="round"
      />
    </svg>
  );
}
export function Landing() {
  const {
    data: services,
    error,
    reload,
    loading,
  } = useResource(() => api<Service[]>("/services"));
  return (
    <>
      <section className="hero container">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="tiny-dot" /> A LITTLE HELP. A HAPPIER HOME.
          </div>
          <h1>
            Good hands.
            <br />A home that
            <br />
            <em>feels like home.</em>
          </h1>
          <p>
            From the small fix you’ve been putting off to a fresh start for your
            garden. Tell us what needs doing — we’ll take it from there.
          </p>
          <div className="hero-actions">
            <ArrowLink to="/request">Request a service</ArrowLink>
            <a href="#services" className="text-link">
              Explore services <ArrowRight size={17} />
            </a>
          </div>
          <div className="local-note">
            <MapPin size={17} /> Bristol & surrounding neighbourhoods{" "}
            <span>·</span> Demo service area
          </div>
        </div>
        <div className="hero-visual">
          <HomeIllustration />
          <div className="art-note">
            <span className="round-icon">
              <HeartHandshake size={25} />
            </span>
            <div>
              <strong>A little care goes a long way.</strong>
              <small>Practical help, thoughtfully handled.</small>
            </div>
          </div>
          <span className="art-caption">
            ILLUSTRATED WITH CARE · FICTIONAL BUSINESS
          </span>
        </div>
      </section>
      <div className="promise-strip">
        <div className="container">
          <span>
            <Check /> Clear, indicative pricing
          </span>
          <span>
            <Check /> Your request, kept in view
          </span>
          <span>
            <Check /> A personal approach
          </span>
        </div>
      </div>
      <section id="services" className="section container">
        <div className="section-heading">
          <div>
            <div className="eyebrow">WHAT CAN WE HELP WITH?</div>
            <h2>Small jobs. Meaningful difference.</h2>
          </div>
          <p>
            Every home is different. Start with a service,
            <br className="desktop-only" /> and tell us what yours needs.
          </p>
        </div>
        {error && (
          <Notice error>
            {error}{" "}
            <button className="text-link" onClick={reload}>
              Try again
            </button>
          </Notice>
        )}
        {loading && !services && <Loading />}
        <div className="service-grid">
          {services?.map((s) => (
            <Link
              key={s.id}
              to={"/request?service=" + s.id}
              className="service-card"
            >
              <span className={"service-icon " + s.category}>
                <ServiceIcon category={s.category} />
              </span>
              <h3>{s.name}</h3>
              <p>{s.description}</p>
              <div className="card-bottom">
                <strong>{s.price}</strong>
                <ArrowRight size={19} />
              </div>
            </Link>
          ))}
        </div>
        <p className="subtle service-pricing">
          Prices are indicative. Scope and a quote are reviewed before any
          booking.
        </p>
      </section>
      <section id="how-it-works" className="how-section">
        <div className="container">
          <div className="section-heading">
            <div>
              <div className="eyebrow">
                LESS BACK-AND-FORTH. MORE PEACE OF MIND.
              </div>
              <h2>A simple way to get things sorted.</h2>
            </div>
          </div>
          <div className="steps">
            {[
              {
                Icon: ClipboardList,
                title: "Tell us what you need",
                text: "Choose a service, describe the job and share a date that suits you.",
              },
              {
                Icon: MessageSquare,
                title: "We review the details",
                text: "Your enquiry moves through review and a quote. Follow along in your dashboard.",
              },
              {
                Icon: HouseIcon,
                title: "Make room for a better home",
                text: "A booking comes after review. Your preferred date is never an automatic appointment.",
              },
            ].map(({ Icon, title, text }, i) => (
              <div className="step" key={title}>
                <div>
                  <Icon size={24} />
                  <span>0{i + 1}</span>
                </div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="container section">
        <div className="cta-band">
          <div>
            <div className="eyebrow">LET’S TAKE ONE THING OFF YOUR LIST.</div>
            <h2>What does your home need?</h2>
            <p>A few details are all it takes to start an enquiry.</p>
          </div>
          <ArrowLink to="/request" className="button light">
            Request a service
          </ArrowLink>
        </div>
      </section>
    </>
  );
}
function HouseIcon({ size }: { size?: number }) {
  return <HeartHandshake size={size} />;
}
