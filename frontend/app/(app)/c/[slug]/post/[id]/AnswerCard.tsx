"use client";

import { useState } from "react";
import Link from "next/link";
import type { JSONContent } from "@tiptap/react";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { VoteWidget } from "@/components/VoteWidget";
import { RichContent } from "@/components/RichContent";
import { SyntrixEditor } from "@/lib/editor/SyntrixEditor";
import { timeAgo } from "@/lib/text";
import styles from "./AnswerCard.module.css";

export interface AnswerData {
  id: string;
  question_id: string;
  author_id: string | null;
  author_handle: string | null;
  author_display_name: string | null;
  author_avatar_url: string | null;
  body_json: Record<string, unknown> | null;
  body_html: string;
  score: number;
  is_accepted: boolean;
  accepted_at: string | null;
  removed_at: string | null;
  created_at: string;
  updated_at: string;
}

interface AnswerCardProps {
  answer: AnswerData;
  isQuestionAuthor: boolean;
  currentUserId: string | null;
  userVote: number;
  onAccept: (answerId: string) => void;
  onUnaccept: (answerId: string) => void;
  onUpdate: (
    answerId: string,
    html: string,
    json: Record<string, unknown>,
  ) => void;
  onDelete: (answerId: string) => void;
}

export function AnswerCard({
  answer,
  isQuestionAuthor,
  currentUserId,
  userVote,
  onAccept,
  onUnaccept,
  onUpdate,
  onDelete,
}: AnswerCardProps) {
  const [editing, setEditing] = useState(false);
  const [editJson, setEditJson] = useState<JSONContent | null>(null);
  const [saving, setSaving] = useState(false);

  const isAuthor = currentUserId && answer.author_id === currentUserId;
  const initials = (answer.author_display_name ?? "?")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  async function handleSaveEdit() {
    if (!editJson) return;
    setSaving(true);
    try {
      const res = await fetch(`/api/answers/${answer.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body_json: editJson }),
      });
      if (res.ok) {
        const updated = await res.json();
        onUpdate(answer.id, updated.body_html, updated.body_json);
        setEditing(false);
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    const res = await fetch(`/api/answers/${answer.id}`, { method: "DELETE" });
    if (res.ok) onDelete(answer.id);
  }

  return (
    <div
      className={`${styles.card} ${answer.is_accepted ? styles.accepted : ""}`}
    >
      <div className={styles.voteCol}>
        <VoteWidget
          targetType="answer"
          targetId={answer.id}
          score={answer.score}
          userVote={userVote}
          layout="vertical"
        />
        {answer.is_accepted && (
          <span className={styles.checkmark} title="Accepted answer">
            ✓
          </span>
        )}
      </div>

      <div className={styles.content}>
        {answer.removed_at && (
          <div className={styles.removedBanner}>
            This answer was removed by a moderator.
          </div>
        )}

        {!answer.removed_at && !editing && (
          <RichContent html={answer.body_html} className={styles.body} />
        )}

        {editing && (
          <div className={styles.editArea}>
            <SyntrixEditor
              initialContent={answer.body_json as JSONContent}
              onChange={(json) => setEditJson(json)}
            />
            <div className={styles.editActions}>
              <Button
                variant="primary"
                onClick={handleSaveEdit}
                disabled={saving}
              >
                {saving ? "Saving..." : "Save"}
              </Button>
              <Button variant="ghost" onClick={() => setEditing(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        <div className={styles.meta}>
          <Avatar
            alt={answer.author_display_name ?? "Unknown"}
            fallback={initials}
            size="xs"
            src={answer.author_avatar_url ?? undefined}
          />
          <span className={styles.authorName}>
            {answer.author_handle ? (
              <Link
                href={`/u/${answer.author_handle}`}
                className={styles.authorLink}
              >
                {answer.author_display_name ?? answer.author_handle}
              </Link>
            ) : (
              "[deleted]"
            )}
          </span>
          <span className={styles.timestamp}>{timeAgo(answer.created_at)}</span>
        </div>

        <div className={styles.actions}>
          {isQuestionAuthor && !answer.removed_at && (
            <>
              {answer.is_accepted ? (
                <button
                  type="button"
                  className={styles.actionBtn}
                  onClick={() => onUnaccept(answer.id)}
                >
                  Unaccept
                </button>
              ) : (
                <button
                  type="button"
                  className={`${styles.actionBtn} ${styles.acceptBtn}`}
                  onClick={() => onAccept(answer.id)}
                >
                  Accept
                </button>
              )}
            </>
          )}
          {isAuthor && !answer.removed_at && (
            <>
              <button
                type="button"
                className={styles.actionBtn}
                onClick={() => setEditing(true)}
              >
                Edit
              </button>
              <button
                type="button"
                className={styles.actionBtn}
                onClick={handleDelete}
              >
                Delete
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
