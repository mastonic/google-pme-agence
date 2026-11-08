export function Logo() {
  return (
    <>
      <svg viewBox="0 0 40 32" width="40" height="32" aria-hidden="true">
        <defs>
          <linearGradient id="lpg" x1="0" y1="1" x2="1" y2="0">
            <stop offset="0" stopColor="#028090" />
            <stop offset="1" stopColor="#00A896" />
          </linearGradient>
        </defs>
        <rect x="3" y="20" width="5" height="8" rx="1" fill="url(#lpg)" />
        <rect x="10" y="15" width="5" height="13" rx="1" fill="url(#lpg)" />
        <rect x="17" y="10" width="5" height="18" rx="1" fill="url(#lpg)" />
        <path d="M2 30 C 14 28, 24 22, 33 8" stroke="#C9A24B" strokeWidth="2" fill="none" strokeLinecap="round" />
        <path d="M28 7 L35 4 L34 12 Z" fill="#00A896" />
      </svg>
      <span className="brand-name">
        <span className="a">PULSE</span>
        <span className="b">LOCALE</span>
        <span className="c">PME</span>
      </span>
    </>
  )
}
