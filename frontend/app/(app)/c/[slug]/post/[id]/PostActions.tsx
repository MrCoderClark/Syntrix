"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import styles from "./PostDetail.module.css";

interface Props {
  postId: string;
  slug: string;
}

export function PostActions({ postId, slug }: Props) {
  const router = useRouter();
  const [removing, setRemoving] = useState(false);

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

  return (
    <div className={styles.actions}>
      <button
        type="button"
        className={styles.actionBtn}
        onClick={() => router.push(`/c/${slug}/post/${postId}/edit`)}
      >
        Edit
      </button>
      <button type="button" className={styles.dangerBtn} onClick={handleDelete}>
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
    </div>
  );
}
