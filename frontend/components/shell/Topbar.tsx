"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { SearchIcon, PlusIcon } from "@/components/icons";
import { Avatar } from "@/components/ui/Avatar";
import styles from "./Topbar.module.css";

interface UserInfo {
  display_name: string;
  avatar_url: string | null;
}

interface TopbarProps {
  onMenuToggle?: () => void;
}

export function Topbar({ onMenuToggle }: TopbarProps) {
  const pathname = usePathname();
  const [user, setUser] = useState<UserInfo | null>(null);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setUser(data);
      })
      .catch(() => {});
  }, []);

  const initials = (user?.display_name ?? "?")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const slugMatch = pathname.match(/^\/c\/([^/]+)/);
  const newPostHref = slugMatch ? `/c/${slugMatch[1]}/submit` : "/communities";

  return (
    <div className={styles.topbar}>
      <button
        className={styles.hamburger}
        onClick={onMenuToggle}
        aria-label="Toggle menu"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path
            d="M3 5h14M3 10h14M3 15h14"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </button>
      <div className={styles.search}>
        <SearchIcon size={16} style={{ color: "var(--ink-faint)" }} />
        <input
          type="text"
          className={styles.searchInput}
          placeholder="Search communities, posts, people..."
          readOnly
        />
      </div>
      <Link href={newPostHref} className={styles.newPostBtn}>
        <PlusIcon />
        New post
      </Link>
      <Link href="/settings/profile">
        <Avatar
          src={user?.avatar_url ?? undefined}
          alt={user?.display_name ?? "profile"}
          fallback={initials}
        />
      </Link>
    </div>
  );
}
