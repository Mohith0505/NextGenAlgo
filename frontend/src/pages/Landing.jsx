import { Link } from "react-router-dom";

const highlights = [
  {
    title: "70+ Broker Connections",
    description: "Link Angel One, Zerodha, Dhan, Fyers, and dozens more with OAuth/TOTP flows.",
    media: "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=960&q=80",
  },
  {
    title: "Multi-Leg Options Builder",
    description: "Visualise IV, Greeks, OI, and build straddles, condors, or custom spreads in one pane.",
    media: "https://images.unsplash.com/photo-1556742049-9083c28f07aa?auto=format&fit=crop&w=960&q=80",
  },
  {
    title: "Institutional RMS",
    description: "Daily loss caps, exposure guardrails, trailing SL, profit lock, and automated square-off.",
    media: "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=960&q=80",
  },
];

const featureGroups = [
  {
    heading: "Trade everything from one terminal",
    copy: "Quick orders, strategy orchestration, RMS, analytics and broker health live in the same workspace—no tab hopping, no relay desktop apps, just your browser.",
    points: [
      "Quick Trade Panel with one-click Buy/Sell, reverse, square-off, and hotkeys.",
      "Option Chain with IV, Greeks, OI/ChgOI, PCR, bias and confidence scoring.",
      "Strategy Engine parity across Backtest · Paper · Live with identical guardrails.",
    ],
    media: "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1000&q=80",
  },
  {
    heading: "Automate your edge",
    copy: "Run built-ins, drop in your Python, or wire TradingView / Amibroker / MT4 / Excel signals. We route them through RMS, allocate lots across accounts, and push fills to your dashboards instantly.",
    points: [
      "Webhook & bridge connectors for TradingView, Amibroker, MT4/5, Excel, Telegram.",
      "Multi-account fan-out with per-account lot allocation and exclusions.",
      "Live logs, trade markers, equity curves, and downloadable compliance exports.",
    ],
    media: "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=1000&q=80",
  },
];

const faq = [
  {
    question: "Is it web-based or do I need a VPS?",
    answer: "100% web-native. No bridge apps or VPS required. Prefer a private deployment? Ship the Docker/K8s stack to your infra in minutes.",
  },
  {
    question: "Which brokers are supported?",
    answer: "Angel One, Zerodha, Dhan, Fyers, Alice Blue, and API-first brokers with adapters. Add accounts from the Brokers workspace.",
  },
  {
    question: "Can I automate external signals?",
    answer: "Yes. Point TradingView webhooks, Amibroker AFL, MT4/5 bridges, Excel, or Python APIs at our endpoint and apply per-account RMS.",
  },
  {
    question: "How do you keep me safe?",
    answer: "Pre-trade checks, daily loss caps, trailing SL, exposure guardrails, auto square-off, immutable logs, and SEBI-ready exports.",
  },
  {
    question: "Do you offer paper trading?",
    answer: "Absolutely. Backtest · Paper · Live share the same engine so behaviour stays consistent before you flip the live switch.",
  },
];

function Landing() {
  return (
    <div className="landing-shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="badge">Next-Gen Algo Terminal</p>
          <h1>Trade faster. Automate smarter. Sleep safer.</h1>
          <p className="lead">
            One browser-based command centre for multi-broker execution, options automation, and
            institutional-grade risk controls. No bridge executables, no VPS, just pro-grade trading
            anywhere.
          </p>
          <div className="actions">
            <Link className="btn primary" to="/auth">Start Free Trial</Link>
            <Link className="btn secondary" to="/auth">View Plans</Link>
            <Link className="btn outline" to="/auth">Login</Link>
          </div>
        </div>
        <div className="hero-media">
          <img
            src="https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=1200&q=80"
            alt="Trading dashboard preview"
          />
        </div>
      </header>

      <section className="section highlights">
        <h2>Why traders switch to Next-Gen</h2>
        <div className="highlight-grid">
          {highlights.map((item) => (
            <article key={item.title} className="highlight-card">
              <div className="media-frame">
                <img src={item.media} alt={item.title} loading="lazy" />
              </div>
              <div>
                <h3>{item.title}</h3>
                <p>{item.description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {featureGroups.map((group) => (
        <section key={group.heading} className="section feature-split">
          <div className="feature-copy">
            <h2>{group.heading}</h2>
            <p>{group.copy}</p>
            <ul>
              {group.points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </div>
          <div className="feature-media">
            <img src={group.media} alt={group.heading} loading="lazy" />
          </div>
        </section>
      ))}

      <section className="section pricing" id="pricing">
        <h2>Pricing & plans</h2>
        <p className="subhead">Start with a 19-day free trial. Upgrade any time.</p>
        <div className="card-grid">
          <article className="card">
            <h3>Starter</h3>
            <p>Paper + live · 1 broker · Core RMS · Quick Trade · Option chain</p>
            <Link to="/auth" className="btn outline small">Choose Starter</Link>
          </article>
          <article className="card">
            <h3>Pro</h3>
            <p>Multi-account · Strategy engine · Advanced RMS · Analytics suite</p>
            <Link to="/auth" className="btn outline small">Choose Pro</Link>
          </article>
          <article className="card">
            <h3>Enterprise</h3>
            <p>SSO · Dedicated support · Data retention controls · Custom limits</p>
            <a href="mailto:hello@nextgenalgo.example" className="btn outline small">Talk to Sales</a>
          </article>
        </div>
      </section>

      <section className="section faq">
        <h2>Frequently asked questions</h2>
        <div className="faq-grid">
          {faq.map((item) => (
            <article key={item.question} className="faq-card">
              <h3>{item.question}</h3>
              <p>{item.answer}</p>
            </article>
          ))}
        </div>
      </section>

      <footer className="section cta">
        <div className="cta-inner">
          <h2>Trade like a pro — without babysitting your terminal.</h2>
          <p>Spin up your trial in minutes, wire your strategies, and let the RMS guard the rest.</p>
          <div className="actions">
            <Link className="btn primary" to="/auth">Start Free Trial</Link>
            <Link className="btn secondary" to="/auth">Login</Link>
            <a className="btn outline" href="mailto:hello@nextgenalgo.example">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Landing;
