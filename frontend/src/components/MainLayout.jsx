import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import Loader from "./Loader";
import { useAuth } from "../hooks/useAuth";

const navLinks = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Broker Management", path: "/brokers" },
  { label: "Quick Trade Panel", path: "/quick-trade" },
  { label: "Execution Groups", path: "/execution-groups" },
  { label: "Option Chain", path: "/option-chain" },
  { label: "Strategies", path: "/strategies" },
  { label: "Risk Management", path: "/risk" },
  { label: "Admin Panel", path: "/admin" },
];

function MainLayout() {
  const location = useLocation();
  const showNav = location.pathname !== "/";
  const { user, initialising, logout } = useAuth();

  if (showNav && !initialising && !user) {
    return <Navigate to="/auth" replace />;
  }

  return (
    <div className="layout-shell">
      {showNav && (
        <aside className="sidebar">
          <Link to="/dashboard" className="brand">
            Next-Gen Algo Terminal
          </Link>
          <nav>
            <ul>
              {navLinks.map(({ label, path }) => (
                <li key={path}>
                  <Link
                    to={path}
                    className={location.pathname.startsWith(path) ? "active" : ""}
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          <div className="sidebar-footer">
            {initialising ? (
              <Loader label="Loading session" />
            ) : user ? (
              <div className="user-summary">
                <div className="user-email">{user.email}</div>
                <button className="btn small outline" type="button" onClick={logout}>
                  Sign Out
                </button>
              </div>
            ) : (
              <p className="muted small">Sign in to continue.</p>
            )}
          </div>
        </aside>
      )}
      <main className={showNav ? "content" : "content-full"}>
        {showNav && initialising ? <Loader label="Initialising" /> : <Outlet />}
      </main>
    </div>
  );
}

export default MainLayout;

