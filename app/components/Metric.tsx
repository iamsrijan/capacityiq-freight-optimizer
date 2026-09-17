import type { MetricIcon } from "../lib/types";

type MetricProps = {
  icon: MetricIcon;
  label: string;
  value: string;
  delta: string;
};

export function Metric({ icon: Icon, label, value, delta }: MetricProps) {
  return (
    <article className="metric-card">
      <div className="metric-icon" aria-hidden="true">
        <Icon size={18} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{delta}</small>
      </div>
    </article>
  );
}
