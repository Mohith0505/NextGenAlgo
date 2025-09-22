export default function BarChart({
  data = [],
  valueKey = "value",
  labelKey = "label",
  maxValue: maxValueOverride,
  formatValue = (value) => value,
}) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <div className="bar-chart bar-chart--empty" aria-hidden>
        <span>No data</span>
      </div>
    );
  }

  const values = data.map((item) => Number(item[valueKey] ?? 0));
  const maxValue =
    typeof maxValueOverride === "number" && Number.isFinite(maxValueOverride)
      ? maxValueOverride
      : Math.max(...values, 1);

  return (
    <div className="bar-chart">
      {data.map((item, index) => {
        const value = Number(item[valueKey] ?? 0);
        const percentage = Math.max(0, Math.min(100, (value / maxValue) * 100));
        const label = item[labelKey] ?? `Item ${index + 1}`;
        return (
          <div key={`${label}-${index}`} className="bar-chart__row">
            <span className="bar-chart__label" title={label}>
              {label}
            </span>
            <div className="bar-chart__track" aria-hidden>
              <div
                className="bar-chart__fill"
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className="bar-chart__value">{formatValue(value)}</span>
          </div>
        );
      })}
    </div>
  );
}

