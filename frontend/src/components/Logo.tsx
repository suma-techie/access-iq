export default function Logo({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path
        d="M12 2L20 5.2V11C20 16.1 16.6 20.4 12 22C7.4 20.4 4 16.1 4 11V5.2L12 2Z"
        fill="var(--color-accent)"
      />
      <path
        d="M12 7.4C10.68 7.4 9.6 8.48 9.6 9.8C9.6 10.77 10.18 11.6 11 11.98V15.4C11 15.95 11.45 16.4 12 16.4C12.55 16.4 13 15.95 13 15.4V11.98C13.82 11.6 14.4 10.77 14.4 9.8C14.4 8.48 13.32 7.4 12 7.4Z"
        fill="var(--color-surface)"
      />
    </svg>
  );
}
