"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import type { SimilarQuestion } from "@/types/similarity";
import { Button } from "@/components/ui/Button";
import styles from "./PostDetail.module.css";

interface Props {
  postId: string;
  slug: string;
  isQuestion?: boolean;
  duplicateOfId?: string | null;
}

export function PostActions({
  postId,
  slug,
  isQuestion,
  duplicateOfId,
}: Props) {
  const router = useRouter();
  const [removing, setRemoving] = useState(false);
  const [showDupModal, setShowDupModal] = useState(false);
  const [dupSearch, setDupSearch] = useState("");
  const [dupResults, setDupResults] = useState<SimilarQuestion[]>([]);
  const [selectedDupId, setSelectedDupId] = useState<string | null>(null);
  const [marking, setMarking] = useState(false);
  const [unmarking, setUnmarking] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function handleDelete() {
    if (!window.confirm("Delete this post? This cannot be undone.")) return;
    const res = await fetch(`/api/posts/${postId}`, { method: "DELETE" });
    if (res.ok) router.push(`/c/${slug}`);
  }

  async function handleRemove() {
    const reason = window.prompt("Reason for removal:");
    if (!reason) return;
    setRemoving(true);
    const res = await fetch(`/api/posts/${postId}/remove`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    });
    setRemoving(false);
    if (res.ok) router.refresh();
  }

  const searchDuplicates = useCallback(
    async (query: string) => {
      if (query.length < 10) {
        setDupResults([]);
        return;
      }
      try {
        const resp = await fetch(
          `/api/communities/${slug}/questions/similar?title=${encodeURIComponent(query)}`,
        );
        if (resp.ok) {
          const data = await resp.json();
          setDupResults(
            data.items.filter((q: SimilarQuestion) => q.id !== postId),
          );
        }
      } catch {
        /* ignore */
      }
    },
    [slug, postId],
  );

  function handleDupSearchChange(value: string) {
    setDupSearch(value);
    setSelectedDupId(null);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => searchDuplicates(value), 300);
  }

  async function handleMarkDuplicate() {
    if (!selectedDupId) return;
    setMarking(true);
    const res = await fetch(`/api/posts/${postId}/mark-duplicate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ duplicate_of_id: selectedDupId }),
    });
    setMarking(false);
    if (res.ok) {
      setShowDupModal(false);
      router.refresh();
    }
  }

  async function handleUnmarkDuplicate() {
    setUnmarking(true);
    const res = await fetch(`/api/posts/${postId}/mark-duplicate`, {
      method: "DELETE",
    });
    setUnmarking(false);
    if (res.ok) router.refresh();
  }

  useEffect(() => {
    if (!showDupModal) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowDupModal(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [showDupModal]);

  return (
    <>
      <div className={styles.actions}>
        <button
          type="button"
          className={styles.actionBtn}
          onClick={() => router.push(`/c/${slug}/post/${postId}/edit`)}
        >
          Edit
        </button>
        <button
          type="button"
          className={styles.dangerBtn}
          onClick={handleDelete}
        >
          Delete
        </button>
        <button
          type="button"
          className={styles.dangerBtn}
          onClick={handleRemove}
          disabled={removing}
        >
          {removing ? "Removing..." : "Mod remove"}
        </button>
        {isQuestion && !duplicateOfId && (
          <button
            type="button"
            className={styles.actionBtn}
            onClick={() => setShowDupModal(true)}
          >
            Mark as duplicate
          </button>
        )}
        {isQuestion && duplicateOfId && (
          <button
            type="button"
            className={styles.actionBtn}
            onClick={handleUnmarkDuplicate}
            disabled={unmarking}
          >
            {unmarking ? "Unmarking..." : "Unmark duplicate"}
          </button>
        )}
      </div>

      {showDupModal && (
        <div className={styles.dupModalOverlay}>
          <div className={styles.dupModal}>
            <h2 className={styles.dupModalTitle}>Mark as duplicate</h2>
            <input
              className={styles.dupSearchInput}
              placeholder="Search for the original question..."
              value={dupSearch}
              onChange={(e) => handleDupSearchChange(e.target.value)}
              autoFocus
            />
            <div className={styles.dupResultList}>
              {dupResults.map((q) => (
                <div
                  key={q.id}
                  className={
                    selectedDupId === q.id
                      ? styles.dupResultItemSelected
                      : styles.dupResultItem
                  }
                  onClick={() => setSelectedDupId(q.id)}
                >
                  {q.title}
                </div>
              ))}
              {dupSearch.length >= 10 && dupResults.length === 0 && (
                <div className={styles.dupResultEmpty}>
                  No matching questions found
                </div>
              )}
            </div>
            <div className={styles.dupModalActions}>
              <Button
                variant="secondary"
                onClick={() => {
                  setShowDupModal(false);
                  setDupSearch("");
                  setDupResults([]);
                  setSelectedDupId(null);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                disabled={!selectedDupId || marking}
                onClick={handleMarkDuplicate}
              >
                {marking ? "Marking..." : "Confirm"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
