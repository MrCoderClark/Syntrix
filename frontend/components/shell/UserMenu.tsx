"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Avatar } from "@/components/ui/Avatar";
import styles from "./UserMenu.module.css";

interface UserInfo {
  handle: string;
  display_name: string;
  avatar_url: string | null;
}

export function UserMenu() {
  const router = useRouter();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setUser(data);
      })
      .catch(() => {});
  }, []);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        close();
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open, close]);

  async function handleLogout() {
    close();
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/signin");
  }

  const initials = (user?.display_name ?? "?")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className={styles.wrapper} ref={ref}>
      <button
        className={styles.trigger}
        onClick={() => setOpen((o) => !o)}
        aria-label="User menu"
      >
        <Avatar
          src={user?.avatar_url ?? undefined}
          alt={user?.display_name ?? "profile"}
          fallback={initials}
        />
      </button>

      {open && (
        <div className={styles.dropdown}>
          {user && (
            <div className={styles.userInfo}>
              <span className={styles.displayName}>{user.display_name}</span>
              <span className={styles.handle}>u/{user.handle}</span>
            </div>
          )}
          <div className={styles.divider} />
          <Link
            href={user ? `/u/${user.handle}` : "/settings/profile"}
            className={styles.item}
            onClick={close}
          >
            My Profile
          </Link>
          <Link
            href="/settings/profile"
            className={styles.item}
            onClick={close}
          >
            Settings
          </Link>
          <div className={styles.divider} />
          <button className={styles.item} onClick={handleLogout}>
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
