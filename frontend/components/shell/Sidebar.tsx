"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Wordmark } from "@/components/Wordmark";
import { HomeIcon, SearchIcon, UserIcon } from "@/components/icons";
import styles from "./Sidebar.module.css";

interface CommunityItem {
  id: string;
  slug: string;
  name: string;
  color: string;
  member_count: number;
}

const NAV_ITEMS = [
  { icon: <HomeIcon />, label: "Feed", href: "/" },
  { icon: <SearchIcon />, label: "Explore", href: "/communities" },
  { icon: <UserIcon />, label: "My profile", href: "/settings/profile" },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const [communities, setCommunities] = useState<CommunityItem[]>([]);

  useEffect(() => {
    fetch("/api/communities/mine")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setCommunities(data))
      .catch(() => {});
  }, []);

  return (
    <aside
      className={`${styles.sidebar}${mobileOpen ? ` ${styles.mobileOpen}` : ""}`}
    >
      <div className={styles.wordmarkWrap}>
        <Wordmark />
      </div>

      <div className={styles.navLabel}>For you</div>
      <ul>
        {NAV_ITEMS.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <li key={item.label}>
              <Link
                href={item.href}
                className={`${styles.navItem}${active ? ` ${styles.active}` : ""}`}
                onClick={onClose}
              >
                <span className={styles.icon}>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>

      <div className={styles.navLabel}>Communities</div>
      <ul>
        {communities.map((c) => {
          const active = pathname.startsWith(`/c/${c.slug}`);
          return (
            <li key={c.id}>
              <Link
                href={`/c/${c.slug}`}
                className={`${styles.communityItem}${active ? ` ${styles.activeCommunity}` : ""}`}
                onClick={onClose}
              >
                <span
                  className={styles.communityDot}
                  style={{ background: c.color }}
                />
                <span>c/{c.slug}</span>
                <span className={styles.members}>{c.member_count}</span>
              </Link>
            </li>
          );
        })}
        {communities.length === 0 && (
          <li>
            <Link
              href="/communities"
              className={styles.communityItem}
              onClick={onClose}
            >
              <span
                className={styles.communityDot}
                style={{ background: "var(--ink-faint)" }}
              />
              <span>Browse communities</span>
            </Link>
          </li>
        )}
      </ul>
    </aside>
  );
}
