function StatCard({ label, value, delta }) {
  return (
    <article className="stat-card">
      <header>
        <p>{label}</p>
        {delta ? <span className={delta > 0 ? "positive" : "negative"}>{delta > 0 ? `+${delta}%` : `${delta}%`}</span> : null}
      </header>
      <strong>{value}</strong>
    </article>
  );
}

export default StatCard;
