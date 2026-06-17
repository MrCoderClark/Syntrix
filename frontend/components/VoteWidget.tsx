"use client";

import { useState } from "react";
import styles from "./VoteWidget.module.css";

interface Props {
  targetType: "post" | "comment";
  targetId: string;
  score: number;
  userVote: number;
  layout?: "vertical" | "horizontal";
}

export function VoteWidget({
  targetType,
  targetId,
  score: initialScore,
  userVote: initialVote,
  layout = "vertical",
}: Props) {
  const [score, setScore] = useState(initialScore);
  const [userVote, setUserVote] = useState(initialVote);
  const [busy, setBusy] = useState(false);

  async function handleVote(value: 1 | -1) {
    if (busy) return;
    const newValue = userVote === value ? 0 : value;
    const scoreDelta = newValue - userVote;

    setScore((s) => s + scoreDelta);
    setUserVote(newValue);
    setBusy(true);

    try {
      const url =
        targetType === "post"
          ? `/api/posts/${targetId}/vote`
          : `/api/comments/${targetId}/vote`;

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: newValue }),
      });

      if (!res.ok) {
        setScore((s) => s - scoreDelta);
        setUserVote(userVote);
      }
    } catch {
      setScore((s) => s - scoreDelta);
      setUserVote(userVote);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className={`${styles.widget} ${layout === "horizontal" ? styles.horizontal : styles.vertical}`}
    >
      <button
        type="button"
        className={`${styles.arrow} ${userVote === 1 ? styles.upActive : ""}`}
        onClick={() => handleVote(1)}
        aria-label="Upvote"
      >
        <svg viewBox="0 0 16 16" className={styles.icon}>
          <path d="M8 3l5 7H3z" />
        </svg>
      </button>
      <span
        className={`${styles.score} ${score > 0 ? styles.positive : score < 0 ? styles.negative : ""}`}
      >
        {score}
      </span>
      <button
        type="button"
        className={`${styles.arrow} ${userVote === -1 ? styles.downActive : ""}`}
        onClick={() => handleVote(-1)}
        aria-label="Downvote"
      >
        <svg viewBox="0 0 16 16" className={styles.icon}>
          <path d="M8 13l5-7H3z" />
        </svg>
      </button>
    </div>
  );
}
