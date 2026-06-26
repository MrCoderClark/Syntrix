"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/Input";
import styles from "./NewDmModal.module.css";

interface UserResult {
  id: string;
  handle: string;
  display_name: string;
  avatar_url: string | null;
}

interface NewDmModalProps {
  onCreated: (roomId: string) => void;
  onClose: () => void;
}

export function NewDmModal({ onCreated, onClose }: NewDmModalProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UserResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [creating, setCreating] = useState<string | null>(null);
  const [error, setError] = useState("");
  const overlayRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const search = useCallback((q: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!q.trim()) {
      setResults([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await fetch(
          `/api/search?q=${encodeURIComponent(q.trim())}`,
        );
        if (res.ok) {
          const data = await res.json();
          setResults(data.users ?? []);
        }
      } finally {
        setSearching(false);
      }
    }, 250);
  }, []);

  const handleSelect = useCallback(
    async (user: UserResult) => {
      setCreating(user.id);
      setError("");
      try {
        const res = await fetch(`/api/dms/${user.id}`, { method: "POST" });
        if (res.ok) {
          const room = await res.json();
          onCreated(room.id);
        } else {
          const data = await res.json().catch(() => null);
          setError(data?.detail ?? "Failed to start conversation");
          setCreating(null);
        }
      } catch {
        setError("Failed to start conversation");
        setCreating(null);
      }
    },
    [onCreated],
  );

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div
      className={styles.overlay}
      ref={overlayRef}
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-dm-title"
      >
        <h3 className={styles.title} id="new-dm-title">
          New message
        </h3>
        <label className={styles.label} htmlFor="dm-search">
          Find a user
        </label>
        <Input
          id="dm-search"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            search(e.target.value);
          }}
          placeholder="Search by name or handle..."
          autoFocus
        />
        <div className={styles.results}>
          {searching && <div className={styles.hint}>Searching...</div>}
          {!searching && query.trim() && results.length === 0 && (
            <div className={styles.hint}>No users found</div>
          )}
          {results.map((user) => (
            <button
              key={user.id}
              className={styles.userRow}
              onClick={() => handleSelect(user)}
              disabled={creating !== null}
            >
              <span className={styles.avatar}>
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt=""
                    className={styles.avatarImg}
                  />
                ) : (
                  (user.display_name[0]?.toUpperCase() ?? "?")
                )}
              </span>
              <span className={styles.userInfo}>
                <span className={styles.displayName}>{user.display_name}</span>
                <span className={styles.handle}>@{user.handle}</span>
              </span>
              {creating === user.id && (
                <span className={styles.hint}>Opening...</span>
              )}
            </button>
          ))}
        </div>
        {error && <div className={styles.error}>{error}</div>}
      </div>
    </div>
  );
}
