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

export function GitHubIcon(props: IconProps) {
  return (
    <svg
      {...defaults(props.size ?? 16, props)}
      strokeWidth={0}
      fill="currentColor"
    >
      <path d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.167 6.839 9.489.5.092.682-.217.682-.482 0-.237-.009-.866-.013-1.7-2.782.603-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.337-2.22-.252-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
    </svg>
  );
}

export function DiscordIcon(props: IconProps) {
  return (
    <svg
      {...defaults(props.size ?? 16, props)}
      strokeWidth={0}
      fill="currentColor"
    >
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.095 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.095 2.157 2.42 0 1.333-.947 2.418-2.157 2.418z" />
    </svg>
  );
}

export function GlobeIcon(props: IconProps) {
  return (
    <svg {...defaults(props.size ?? 16, props)}>
      <circle cx="12" cy="12" r="10" />
      <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10A15.3 15.3 0 0 1 12 2z" />
    </svg>
  );
}
