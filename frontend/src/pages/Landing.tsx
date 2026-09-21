import { useNavigate } from "react-router-dom";
import Logo from "../components/Logo";
import { useAuth } from "../context/AuthContext";

const FEATURES = [
  {
    kicker: "Grounded in evidence",
    title: "Nothing granted on a hunch.",
    body:
      "Every approval traces back to a citation — an assigned ADO task, an uploaded doc, or an exact catalog match. If the agent can't find evidence, it says so instead of pretending.",
  },
  {
    kicker: "Built for real orgs",
    title: "Approvals that match how your team actually works.",
    body:
      "Team Leads and Application Owners see exactly what's theirs. Managers back up every decision org-wide. Delegation covers the gaps when someone's out.",
  },
  {
    kicker: "Always visible",
    title: "See the whole system, instantly.",
    body:
      "Live analytics on every request, every approval, every turnaround — split by severity, by application, by how much of the load the agent absorbed on its own.",
  },
];

export default function Landing() {
  const { user } = useAuth();
  const navigate = useNavigate();

  function handleCta() {
    navigate(user ? "/dashboard" : "/login");
  }

  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <div className="landing-nav-brand">
          <Logo size={22} />
          <span>AccessIQ</span>
        </div>
        <button className="landing-login-button" onClick={handleCta}>
          {user ? "Dashboard" : "Log in"}
        </button>
      </nav>

      <section className="landing-hero">
        <p className="landing-hero-kicker">Access control, reasoned about.</p>
        <h1 className="landing-hero-title">
          Access,
          <br />
          decided in seconds.
        </h1>
        <p className="landing-hero-subtitle">
          AccessIQ grounds every permission request in real evidence — tasks, documents, and your own catalog —
          before anyone approves anything.
        </p>
        <button className="landing-hero-cta" onClick={handleCta}>
          {user ? "Go to dashboard" : "Log in"}
        </button>
      </section>

      {FEATURES.map((f, i) => (
        <section key={f.title} className={`landing-feature ${i % 2 === 1 ? "landing-feature-alt" : ""}`}>
          <div className="landing-feature-inner">
            <p className="landing-feature-kicker">{f.kicker}</p>
            <h2 className="landing-feature-title">{f.title}</h2>
            <p className="landing-feature-body">{f.body}</p>
          </div>
        </section>
      ))}

      <section className="landing-closing">
        <h2 className="landing-closing-title">Stop approving on faith.</h2>
        <button className="landing-hero-cta" onClick={handleCta}>
          {user ? "Go to dashboard" : "Log in"}
        </button>
      </section>

      <footer className="landing-footer">
        <span>© {new Date().getFullYear()} AccessIQ</span>
      </footer>
    </div>
  );
}
