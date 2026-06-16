import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function defaults(size: number, props: IconProps): SVGProps<SVGSVGElement> {
  const { size: _size, ...rest } = props;
  return {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    ...rest,
  };
}

export function HomeIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 18, props)}>
      <path d="M3 13l9-9 9 9M5 12v8h14v-8" />
    </svg>
  );
}

export function SearchIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 18, props)}>
      <circle cx="11" cy="11" r="6" />
      <path d="m20 20-4-4" />
    </svg>
  );
}

export function BellIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 18, props)}>
      <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M14 19a2 2 0 1 1-4 0" />
    </svg>
  );
}

export function UserIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 18, props)}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </svg>
  );
}

export function PlusIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 14, props)} strokeWidth={2.4}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function FilterIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 14, props)}>
      <path d="M3 6h18M6 12h12M10 18h4" />
    </svg>
  );
}

export function CommentIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 14, props)}>
      <path d="M21 12a8 8 0 0 1-12.5 6.6L3 21l2-4.5A8 8 0 1 1 21 12z" />
    </svg>
  );
}

export function BookmarkIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 14, props)}>
      <path d="M19 21V8a2 2 0 0 0-2-2h-3l-2-3-2 3H7a2 2 0 0 0-2 2v13l7-3z" />
    </svg>
  );
}

export function MessageIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 18, props)}>
      <path d="M21 12a8.5 8.5 0 1 1-3.6-6.9L21 4l-1 4.4A8.5 8.5 0 0 1 21 12z" />
    </svg>
  );
}

export function UpArrow(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 14, props)} strokeWidth={2.2}>
      <path d="M12 5l7 7H5z" />
    </svg>
  );
}

export function DownArrow(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 14, props)} strokeWidth={2.2}>
      <path d="M12 19l7-7H5z" />
    </svg>
  );
}
