interface CardArtProps {
  color: string;
  id: string;
}

export function CardArt({ color, id }: CardArtProps) {
  return (
    <svg
      viewBox="0 0 640 360"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="xMidYMid slice"
      style={{ width: "100%", height: "100%", display: "block" }}
    >
      <defs>
        <radialGradient id={`${id}-ga`} cx="25%" cy="35%" r="0.7">
          <stop offset="0%" stopColor="#ffffff" stopOpacity={0.3} />
          <stop offset="60%" stopColor={color} stopOpacity={0} />
        </radialGradient>
        <radialGradient id={`${id}-gb`} cx="75%" cy="75%" r="0.6">
          <stop offset="0%" stopColor="#ffffff" stopOpacity={0.15} />
          <stop offset="55%" stopColor={color} stopOpacity={0} />
        </radialGradient>
        <filter id={`${id}-grain`}>
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.85"
            numOctaves={2}
            stitchTiles="stitch"
          />
          <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.35 0" />
        </filter>
      </defs>
      <rect width="100%" height="100%" fill={color} />
      <rect width="100%" height="100%" fill={`url(#${id}-ga)`} />
      <rect width="100%" height="100%" fill={`url(#${id}-gb)`} />
      <rect
        width="100%"
        height="100%"
        filter={`url(#${id}-grain)`}
        opacity={0.7}
        style={{ mixBlendMode: "overlay" }}
      />
    </svg>
  );
}
