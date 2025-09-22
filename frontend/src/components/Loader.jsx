function Loader({ label = "Loading" }) {
  return (
    <div className="loader">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export default Loader;
