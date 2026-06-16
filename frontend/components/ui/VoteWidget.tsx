"use client";

import { UpArrow, DownArrow } from "@/components/icons";
import styles from "./VoteWidget.module.css";

interface VoteWidgetProps {
  score: number;
  userVote?: 1 | 0 | -1;
  onUpvote?: () => void;
  onDownvote?: () => void;
}

export function VoteWidget({
  score,
  userVote = 0,
  onUpvote,
  onDownvote,
}: VoteWidgetProps) {
  return (
    <div className={styles.vote}>
      <button
        className={`${styles.voteBtn} ${styles.up}${userVote === 1 ? ` ${styles.upActive}` : ""}`}
        aria-label="upvote"
        onClick={onUpvote}
      >
        <UpArrow />
      </button>
      <span className={styles.score}>{score}</span>
      <button
        className={`${styles.voteBtn} ${styles.dn}${userVote === -1 ? ` ${styles.dnActive}` : ""}`}
        aria-label="downvote"
        onClick={onDownvote}
      >
        <DownArrow />
      </button>
    </div>
  );
}
