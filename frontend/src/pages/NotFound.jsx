import { Link } from "react-router-dom";

function NotFound() {
  return (
    <section className="page">
      <h1>Page Not Found</h1>
      <p>The requested route is not part of the current build.</p>
      <Link to="/" className="btn secondary">
        Return to Landing
      </Link>
    </section>
  );
}

export default NotFound;
