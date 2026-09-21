export default function SecurityIllustration() {
  return (
    <svg viewBox="0 0 480 480" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <radialGradient id="glow" cx="50%" cy="42%" r="60%">
          <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.35" />
          <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="lockBody" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--color-accent)" />
          <stop offset="100%" stopColor="color-mix(in srgb, var(--color-accent) 60%, #1c1c1c)" />
        </linearGradient>
      </defs>

      <circle cx="240" cy="220" r="230" fill="url(#glow)" />

      {}
      <circle cx="240" cy="220" r="190" fill="none" stroke="var(--color-border)" strokeWidth="1" strokeDasharray="2 8" />
      <circle cx="240" cy="220" r="140" fill="none" stroke="var(--color-border)" strokeWidth="1" strokeDasharray="2 8" />

      {}
      <g stroke="var(--color-border)" strokeWidth="1.2">
        <line x1="240" y1="220" x2="90" y2="120" />
        <line x1="240" y1="220" x2="410" y2="140" />
        <line x1="240" y1="220" x2="80" y2="330" />
        <line x1="240" y1="220" x2="400" y2="340" />
      </g>
      <g fill="var(--color-accent)">
        <circle cx="90" cy="120" r="6" />
        <circle cx="410" cy="140" r="5" />
        <circle cx="80" cy="330" r="5" />
        <circle cx="400" cy="340" r="6" />
      </g>

      {}
      <path
        d="M190 200V165C190 130 213 105 240 105C267 105 290 130 290 165V200"
        fill="none"
        stroke="url(#lockBody)"
        strokeWidth="22"
        strokeLinecap="round"
      />

      {}
      <rect x="150" y="195" width="180" height="150" rx="24" fill="url(#lockBody)" />

      {}
      <circle cx="240" cy="255" r="16" fill="var(--color-bg)" />
      <path d="M232 268L248 268L242 300L238 300Z" fill="var(--color-bg)" />
    </svg>
  );
}
