"use client";

import { useState } from "react";
import type { JSONContent } from "@tiptap/react";
import { Avatar } from "@/components/ui/Avatar";
import { VoteWidget } from "@/components/VoteWidget";
import { CommentEditor } from "@/lib/editor/CommentEditor";
import { timeAgo } from "@/lib/text";
import styles from "./Comments.module.css";

export interface CommentData {
  id: string;
  post_id: string;
  author_id: string | null;
  author_handle: string | null;
  author_display_name: string | null;
  author_avatar_url: string | null;
  parent_id: string | null;
  depth: number;
  body_html: string;
  score: number;
  deleted_at: string | null;
  removed_at: string | null;
  created_at: string;
  children: CommentData[];
}

interface Props {
  comment: CommentData;
  postId: string;
  onReplyPosted: () => void;
}

export function CommentNode({ comment, postId, onReplyPosted }: Props) {
  const [replying, setReplying] = useState(false);
  const [replyJson, setReplyJson] = useState<JSONContent | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const isDeleted = !!comment.deleted_at;
  const isRemoved = !!comment.removed_at;
  const showCollapsed = comment.depth > 6;

  const initials = (comment.author_display_name ?? "?")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  async function handleReply() {
    if (!replyJson || submitting) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/posts/${postId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          body_json: replyJson,
          parent_comment_id: comment.id,
        }),
      });
      if (res.ok) {
        setReplying(false);
        setReplyJson(null);
        onReplyPosted();
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className={`${styles.node} ${showCollapsed ? styles.collapsed : ""}`}
      style={{ "--depth": comment.depth } as React.CSSProperties}
    >
      <div className={styles.thread}>
        <div className={styles.header}>
          {!isDeleted && !isRemoved && (
            <Avatar
              alt={comment.author_display_name ?? "Unknown"}
              fallback={initials}
              size="xs"
              src={comment.author_avatar_url ?? undefined}
            />
          )}
          <span className={styles.authorName}>
            {isDeleted ? (
              "[deleted]"
            ) : isRemoved ? (
              "[removed]"
            ) : comment.author_handle ? (
              <a
                href={`/u/${comment.author_handle}`}
                className={styles.authorLink}
              >
                {comment.author_display_name ?? comment.author_handle}
              </a>
            ) : (
              "[unknown]"
            )}
          </span>
          <span className={styles.dot}>·</span>
          <span className={styles.time}>{timeAgo(comment.created_at)}</span>
        </div>

        <div
          className={styles.body}
          dangerouslySetInnerHTML={{ __html: comment.body_html }}
        />

        {!isDeleted && !isRemoved && (
          <div className={styles.commentActions}>
            <VoteWidget
              targetType="comment"
              targetId={comment.id}
              score={comment.score}
              userVote={0}
              layout="horizontal"
            />
            <button
              type="button"
              className={styles.replyBtn}
              onClick={() => setReplying(!replying)}
            >
              {replying ? "Cancel" : "Reply"}
            </button>
          </div>
        )}

        {replying && (
          <div className={styles.replyBox}>
            <CommentEditor
              placeholder={`Reply to ${comment.author_display_name ?? "comment"}...`}
              onChange={setReplyJson}
              onSubmit={handleReply}
            />
          </div>
        )}
      </div>

      {comment.children.length > 0 && (
        <div className={styles.children}>
          {comment.children.map((child) => (
            <CommentNode
              key={child.id}
              comment={child}
              postId={postId}
              onReplyPosted={onReplyPosted}
            />
          ))}
        </div>
      )}
    </div>
  );
}
