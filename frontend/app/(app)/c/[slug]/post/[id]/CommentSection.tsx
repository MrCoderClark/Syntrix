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
  const [rootJson, setRootJson] = useState<JSONContent | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchComments = useCallback(async () => {
    const res = await fetch(`/api/posts/${postId}/comments`);
    if (res.ok) {
      const data = await res.json();
      setComments(data.comments);
      setTotalCount(data.total_count);
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
          placeholder="Add a comment..."
          onChange={setRootJson}
          onSubmit={handleRootSubmit}
        />
      </div>

      {loading ? (
        <p className={styles.loading}>Loading comments...</p>
      ) : comments.length === 0 ? (
        <p className={styles.empty}>No comments yet. Be the first!</p>
      ) : (
        <div className={styles.tree}>
          {comments.map((c) => (
            <CommentNode
              key={c.id}
              comment={c}
              postId={postId}
              onReplyPosted={fetchComments}
            />
          ))}
        </div>
      )}
    </section>
  );
}
