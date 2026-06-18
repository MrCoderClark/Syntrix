"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { SearchIcon, PlusIcon } from "@/components/icons";
import { UserMenu } from "./UserMenu";
import styles from "./Topbar.module.css";

interface TopbarProps {
  onMenuToggle?: () => void;
}

export function Topbar({ onMenuToggle }: TopbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [query, setQuery] = useState("");

  const slugMatch = pathname.match(/^\/c\/([^/]+)/);
  const newPostHref = slugMatch ? `/c/${slugMatch[1]}/submit` : "/communities";

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (q) {
      router.push(`/search?q=${encodeURIComponent(q)}`);
    }
  }

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
      <form className={styles.search} onSubmit={handleSearch}>
        <SearchIcon size={16} style={{ color: "var(--ink-faint)" }} />
        <input
          type="text"
          className={styles.searchInput}
          placeholder="Search communities, posts, people..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </form>
      <Link href={newPostHref} className={styles.newPostBtn}>
        <PlusIcon />
        New post
      </Link>
      <UserMenu />
    </div>
  );
}
