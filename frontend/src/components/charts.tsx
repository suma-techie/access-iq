import { useState } from "react";
import type { ReactNode } from "react";
import { chrome } from "../theme/colors";

export function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>{title}</h3>
        {subtitle && <span className="chart-card-subtitle">{subtitle}</span>}
      </div>
      {children}
    </div>
  );
}

interface BarDatum {
  label: string;
  value: number;
  color?: string;
}

export function BarChart({
  data,
  color = "#3987e5",
  height = 180,
  formatValue = (v: number) => String(v),
}: {
  data: BarDatum[];
  color?: string;
  height?: number;
  formatValue?: (v: number) => string;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  if (data.length === 0) {
    return <p className="chart-empty">No data yet.</p>;
  }
  const max = Math.max(...data.map((d) => d.value), 1);
  const barWidth = 100 / data.length;

  return (
    <div className="bar-chart">
      <svg viewBox={`0 0 100 ${height}`} preserveAspectRatio="none" className="bar-chart-svg">
        <line x1="0" y1={height - 20} x2="100" y2={height - 20} stroke={chrome.baseline} strokeWidth="0.5" />
        {data.map((d, i) => {
          const barHeight = (d.value / max) * (height - 30);
          const x = i * barWidth + barWidth * 0.15;
          const w = barWidth * 0.7;
          const y = height - 20 - barHeight;
          const fill = d.color ?? color;
          return (
            <g key={d.label} onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}>
              <rect
                x={x}
                y={y}
                width={w}
                height={Math.max(barHeight, 1)}
                rx="1.2"
                fill={fill}
                opacity={hovered === null || hovered === i ? 1 : 0.45}
              />
              <text x={x + w / 2} y={y - 3} textAnchor="middle" fontSize="5" fill={chrome.secondaryInk}>
                {d.value > 0 ? formatValue(d.value) : ""}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="bar-chart-labels">
        {data.map((d, i) => (
          <span key={d.label} className={hovered === i ? "bar-chart-label active" : "bar-chart-label"}>
            {d.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export function LineChart({
  data,
  color = "#3987e5",
  height = 180,
}: {
  data: { label: string; value: number }[];
  color?: string;
  height?: number;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  if (data.length === 0) {
    return <p className="chart-empty">No data yet.</p>;
  }
  const max = Math.max(...data.map((d) => d.value), 1);
  const stepX = data.length > 1 ? 100 / (data.length - 1) : 0;
  const points = data.map((d, i) => {
    const x = data.length > 1 ? i * stepX : 50;
    const y = height - 20 - (d.value / max) * (height - 30);
    return { x, y, ...d };
  });
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const areaPath = `${linePath} L${points[points.length - 1].x},${height - 20} L${points[0].x},${height - 20} Z`;

  return (
    <div className="bar-chart">
      <svg viewBox={`0 0 100 ${height}`} preserveAspectRatio="none" className="bar-chart-svg">
        <line x1="0" y1={height - 20} x2="100" y2={height - 20} stroke={chrome.baseline} strokeWidth="0.5" />
        <path d={areaPath} fill={color} opacity={0.12} stroke="none" />
        <path d={linePath} fill="none" stroke={color} strokeWidth="1" vectorEffect="non-scaling-stroke" />
        {points.map((p, i) => (
          <g key={p.label} onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}>
            <circle cx={p.x} cy={p.y} r={hovered === i ? 2 : 1.2} fill={color} />
            <rect x={p.x - stepX / 2} y="0" width={Math.max(stepX, 2)} height={height - 20} fill="transparent" />
          </g>
        ))}
      </svg>
      {hovered !== null && (
        <div className="chart-tooltip-inline">
          <strong>{points[hovered].label}</strong> — {points[hovered].value} request{points[hovered].value === 1 ? "" : "s"}
        </div>
      )}
    </div>
  );
}

interface PieDatum {
  label: string;
  value: number;
  color: string;
}

export function DonutChart({
  data,
  size = 180,
  centerLabel = "Total",
}: {
  data: PieDatum[];
  size?: number;
  centerLabel?: string;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (total === 0) {
    return <p className="chart-empty">No data yet.</p>;
  }

  const radius = 40;
  const strokeWidth = 16;
  const circumference = 2 * Math.PI * radius;
  let cumulative = 0;

  const segments = data
    .filter((d) => d.value > 0)
    .map((d, i) => {
      const fraction = d.value / total;
      const dash = fraction * circumference;
      const gap = 1.5; 
      const offset = -cumulative;
      cumulative += dash;
      return { ...d, dash: Math.max(dash - gap, 0), offset, index: i, fraction };
    });

  const activeSegment = hovered !== null ? segments[hovered] : null;

  return (
    <div className="donut-chart">
      <svg viewBox="0 0 100 100" width={size} height={size}>
        <g transform="rotate(-90 50 50)">
          <circle cx="50" cy="50" r={radius} fill="none" stroke="var(--chart-grid)" strokeWidth={strokeWidth} />
          {segments.map((s) => (
            <circle
              key={s.label}
              cx="50"
              cy="50"
              r={radius}
              fill="none"
              stroke={s.color}
              strokeWidth={strokeWidth}
              strokeDasharray={`${s.dash} ${circumference - s.dash}`}
              strokeDashoffset={s.offset}
              opacity={hovered === null || hovered === s.index ? 1 : 0.35}
              style={{ transition: "opacity 0.15s ease" }}
              onMouseEnter={() => setHovered(s.index)}
              onMouseLeave={() => setHovered(null)}
            />
          ))}
        </g>
        <text x="50" y="47" textAnchor="middle" fontSize="13" fontWeight="700" fill="var(--color-text)">
          {activeSegment ? activeSegment.value : total}
        </text>
        <text x="50" y="59" textAnchor="middle" fontSize="6.5" fill="var(--color-muted)">
          {activeSegment ? activeSegment.label : centerLabel}
        </text>
      </svg>
      <div className="chart-legend">
        {data
          .filter((d) => d.value > 0)
          .map((d, i) => (
            <span
              key={d.label}
              className="chart-legend-item"
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              style={{ opacity: hovered === null || hovered === i ? 1 : 0.5, cursor: "default" }}
            >
              <span className="chart-legend-swatch" style={{ background: d.color }} />
              {d.label} ({d.value})
            </span>
          ))}
      </div>
    </div>
  );
}

export function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat-tile">
      <span className="stat-tile-value">{value}</span>
      <span className="stat-tile-label">{label}</span>
    </div>
  );
}
