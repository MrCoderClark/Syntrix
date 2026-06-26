"use client";

import { PencilIcon, TrashIcon } from "@/components/icons";
import styles from "./MessageActions.module.css";

interface MessageActionsProps {
  isOwn: boolean;
  onEdit?: () => void;
  onDelete: () => void;
}

export function MessageActions({
  isOwn,
  onEdit,
  onDelete,
}: MessageActionsProps) {
  return (
    <div className={styles.actions}>
      {isOwn && onEdit && (
        <button
          className={styles.actionBtn}
          onClick={onEdit}
          title="Edit"
          aria-label="Edit message"
        >
          <PencilIcon />
        </button>
      )}
      <button
        className={styles.actionBtn}
        onClick={onDelete}
        title="Delete"
        aria-label="Delete message"
      >
        <TrashIcon />
      </button>
    </div>
  );
}
