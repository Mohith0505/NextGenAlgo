export default function HeatmapGrid({
  cells = [],
  maxValue: explicitMax,
  formatValue = (value) => value,
}) {
  if (!Array.isArray(cells) || cells.length === 0) {
    return (
      <div className="heatmap heatmap--empty" aria-hidden>
        <span>No data</span>
      </div>
    );
  }

  const values = cells.map((cell) => Number(cell.value ?? 0));
  const maxValue =
    typeof explicitMax === "number" && Number.isFinite(explicitMax)
      ? explicitMax
      : Math.max(...values, 1);

  return (
    <div className="heatmap" role="group" aria-label="Heatmap breakdown">
      {cells.map((cell, index) => {
        const value = Number(cell.value ?? 0);
        const intensity = Math.max(0, Math.min(1, value / maxValue));
        const lightness = 90 - intensity * 45;
        const background = `hsl(210, 90%, ${lightness.toFixed(1)}%)`;
        const label = cell.label ?? `Bucket ${index + 1}`;
        return (
          <div key={`${label}-${index}`} className="heatmap__cell" style={{ background }}>
            <span className="heatmap__label">{label}</span>
            <span className="heatmap__value">{formatValue(value)}</span>
          </div>
        );
      })}
    </div>
  );
}
