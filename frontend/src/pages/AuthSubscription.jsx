import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import NotificationBanner from "../components/NotificationBanner";
import Loader from "../components/Loader";
import { useAuth } from "../hooks/useAuth";

const initialForm = {
  name: "",
  email: "",
  password: "",
  phone: "",
};

function AuthSubscription() {
  const { user, login, register, initialising } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [formState, setFormState] = useState(initialForm);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!initialising && user) {
      navigate("/dashboard", { replace: true });
    }
  }, [user, initialising, navigate]);

  function updateField(field, value) {
    setFormState((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login({ email: formState.email, password: formState.password });
        setMessage("Login successful. Redirecting...");
      } else {
        if (!formState.name.trim()) {
          throw new Error("Please provide your full name.");
        }
        await register({
          name: formState.name,
          email: formState.email,
          password: formState.password,
          phone: formState.phone || undefined,
        });
        setMessage("Account created. Redirecting...");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (initialising && !user) {
    return (
      <section className="page">
        <Loader label="Preparing authentication" />
      </section>
    );
  }

  return (
    <section className="page">
      <h1>{mode === "login" ? "Sign In" : "Create Account"}</h1>
      <p>
        Access the Next-Gen Algo Terminal using your seeded demo credentials. Registration is
        limited to the Phase 1 flow and will be replaced with full subscription onboarding later.
      </p>

      {error && <NotificationBanner type="danger" message={error} />}
      {message && <NotificationBanner type="info" message={message} />}

      <div className="card-grid">
        <div className="card">
          <form className="form-grid" onSubmit={handleSubmit}>
            {mode === "register" && (
              <label className="form-control">
                <span>Full Name</span>
                <input
                  type="text"
                  value={formState.name}
                  onChange={(event) => updateField("name", event.target.value)}
                  required
                />
              </label>
            )}
            <label className="form-control">
              <span>Email</span>
              <input
                type="email"
                value={formState.email}
                onChange={(event) => updateField("email", event.target.value)}
                required
              />
            </label>
            {mode === "register" && (
              <label className="form-control">
                <span>Phone (optional)</span>
                <input
                  type="tel"
                  value={formState.phone}
                  onChange={(event) => updateField("phone", event.target.value)}
                />
              </label>
            )}
            <label className="form-control">
              <span>Password</span>
              <input
                type="password"
                value={formState.password}
                onChange={(event) => updateField("password", event.target.value)}
                required
                minLength={6}
              />
            </label>
            <button className="btn primary" type="submit" disabled={submitting}>
              {submitting ? "Please wait..." : mode === "login" ? "Sign In" : "Register"}
            </button>
          </form>
        </div>
        <div className="card">
          <h2>Need a different action?</h2>
          <p>
            {mode === "login"
              ? "Don't have an account yet?"
              : "Already registered with the seeded environment?"}
          </p>
          <button
            className="btn secondary"
            type="button"
            onClick={() => {
              setMode((prev) => (prev === "login" ? "register" : "login"));
              setError("");
              setMessage("");
            }}
          >
            {mode === "login" ? "Create Account" : "Back to Sign In"}
          </button>
        </div>
      </div>
    </section>
  );
}

export default AuthSubscription;
