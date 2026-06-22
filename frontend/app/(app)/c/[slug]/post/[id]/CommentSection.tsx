"use client";

import { useCallback, useEffect, useState } from "react";
import type { JSONContent } from "@tiptap/react";
import { CommentEditor } from "@/lib/editor/CommentEditor";
import { CommentNode } from "./CommentNode";
import type { CommentData } from "./CommentNode";
import styles from "./Comments.module.css";

interface Props {
  postId: string;
}

export function CommentSection({ postId }: Props) {
  const [comments, setComments] = useState<CommentData[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [commentVotes, setCommentVotes] = useState<Record<string, number>>({});
  const [rootJson, setRootJson] = useState<JSONContent | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [editorKey, setEditorKey] = useState(0);

  function collectCommentIds(commentList: CommentData[]): string[] {
    const ids: string[] = [];
    for (const c of commentList) {
      ids.push(c.id);
      if (c.children.length > 0) ids.push(...collectCommentIds(c.children));
    }
    return ids;
  }

  async function fetchCommentVotes(commentList: CommentData[]) {
    const ids = collectCommentIds(commentList);
    if (ids.length === 0) return;
    const params = new URLSearchParams({
      target_type: "comment",
      target_ids: ids.slice(0, 50).join(","),
    });
    try {
      const res = await fetch(`/api/votes/mine?${params}`);
      if (res.ok) {
        const data = await res.json();
        setCommentVotes(data.votes ?? {});
      }
    } catch {
      /* ignore */
    }
  }

  const fetchComments = useCallback(async () => {
    setError(false);
    try {
      const res = await fetch(`/api/posts/${postId}/comments`);
      if (res.ok) {
        const data = await res.json();
        setComments(data.comments);
        setTotalCount(data.total_count);
        await fetchCommentVotes(data.comments);
      } else {
        setError(true);
      }
    } catch {
      setError(true);
    }
    setLoading(false);
  }, [postId]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  async function handleRootSubmit() {
    if (!rootJson || submitting) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/posts/${postId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body_json: rootJson }),
      });
      if (res.ok) {
        setRootJson(null);
        setEditorKey((k) => k + 1);
        fetchComments();
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>
        {totalCount} {totalCount === 1 ? "Comment" : "Comments"}
      </h2>

      <div className={styles.rootEditor}>
        <CommentEditor
          key={editorKey}
          placeholder="Add a comment..."
          onChange={setRootJson}
          onSubmit={handleRootSubmit}
        />
      </div>

      {loading ? (
        <p className={styles.loading}>Loading comments...</p>
      ) : error ? (
        <p className={styles.empty}>
          Failed to load comments.{" "}
          <button onClick={fetchComments} className={styles.retryBtn}>
            Try again
          </button>
        </p>
      ) : comments.length === 0 ? (
        <p className={styles.empty}>No comments yet. Be the first!</p>
      ) : (
        <div className={styles.tree}>
          {comments.map((c) => (
            <CommentNode
              key={c.id}
              comment={c}
              postId={postId}
              commentVotes={commentVotes}
              onReplyPosted={fetchComments}
            />
          ))}
        </div>
      )}
    </section>
  );
}
