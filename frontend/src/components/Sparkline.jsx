function buildPath(points, width, height) {
  if (points.length === 0) {
    return "";
  }

  return points
    .map((point, index) => {
      const delimiter = index === 0 ? "M" : "L";
      return `${delimiter}${point.x},${point.y}`;
    })
    .join(" ");
}

function buildArea(points, width, height) {
  if (points.length === 0) {
    return "";
  }

  const start = `M0,${height}`;
  const middle = points.map((point) => `L${point.x},${point.y}`).join(" ");
  const end = `L${width},${height} Z`;
  return `${start} ${middle} ${end}`;
}

export default function Sparkline({
  data = [],
  width = 240,
  height = 80,
  stroke = "#0ea5e9",
  fill = "rgba(14, 165, 233, 0.15)",
  valueExtractor = (point) => Number(point.y ?? point.value ?? 0),
}) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <div className="sparkline sparkline--empty" aria-hidden>
        <span>No data</span>
      </div>
    );
  }

  const values = data.map((point) => valueExtractor(point));
  const minValue = Math.min(...values, 0);
  const maxValue = Math.max(...values, 0);
  const span = maxValue - minValue || 1;

  const points = data.map((point, index) => {
    const x = (index / Math.max(data.length - 1, 1)) * width;
    const yValue = valueExtractor(point);
    const normalizedY = height - ((yValue - minValue) / span) * height;
    return { x: Number(x.toFixed(2)), y: Number(normalizedY.toFixed(2)) };
  });

  const pathD = buildPath(points, width, height);
  const areaD = buildArea(points, width, height);

  return (
    <svg
      className="sparkline"
      role="img"
      aria-label="Sparkline chart"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
    >
      <path d={areaD} fill={fill} />
      <path d={pathD} fill="none" stroke={stroke} strokeWidth={2} strokeLinejoin="round" />
    </svg>
  );
}

