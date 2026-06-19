"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { timeAgo, stripHtml } from "@/lib/text";
import styles from "./ProfileTabs.module.css";

interface PostItem {
  id: string;
  title: string;
  score: number;
  comment_count: number;
  community_slug: string;
  community_name: string;
  created_at: string;
}

interface CommentItem {
  id: string;
  body_html: string;
  score: number;
  post_id: string;
  post_title: string;
  community_slug: string;
  created_at: string;
}

interface ActivityResponse<T> {
  items: T[];
  total: number;
}

export function ProfileTabs({ handle }: { handle: string }) {
  const [tab, setTab] = useState<"posts" | "comments">("posts");
  const [posts, setPosts] = useState<ActivityResponse<PostItem> | null>(null);
  const [comments, setComments] =
    useState<ActivityResponse<CommentItem> | null>(null);

  useEffect(() => {
    if (tab === "posts" && !posts) {
      fetch(`/api/users/${handle}/posts?limit=20`)
        .then((r) => (r.ok ? r.json() : { items: [], total: 0 }))
        .then(setPosts)
        .catch(() => setPosts({ items: [], total: 0 }));
    }
    if (tab === "comments" && !comments) {
      fetch(`/api/users/${handle}/comments?limit=20`)
        .then((r) => (r.ok ? r.json() : { items: [], total: 0 }))
        .then(setComments)
        .catch(() => setComments({ items: [], total: 0 }));
    }
  }, [tab, handle, posts, comments]);

  return (
    <div className={styles.tabs}>
      <div className={styles.tabStrip}>
        <button
          className={`${styles.tabBtn} ${tab === "posts" ? styles.active : ""}`}
          onClick={() => setTab("posts")}
        >
          Posts
        </button>
        <button
          className={`${styles.tabBtn} ${tab === "comments" ? styles.active : ""}`}
          onClick={() => setTab("comments")}
        >
          Comments
        </button>
      </div>

      {tab === "posts" && (
        <div className={styles.list}>
          {!posts ? (
            <p className={styles.loading}>Loading...</p>
          ) : posts.items.length === 0 ? (
            <p className={styles.empty}>No posts yet</p>
          ) : (
            posts.items.map((p) => (
              <Link
                key={p.id}
                href={`/c/${p.community_slug}/post/${p.id}`}
                className={styles.card}
              >
                <div className={styles.cardTop}>
                  <span className={styles.community}>c/{p.community_slug}</span>
                  <span className={styles.dot}>&middot;</span>
                  <span className={styles.time}>{timeAgo(p.created_at)}</span>
                </div>
                <div className={styles.cardTitle}>{p.title}</div>
                <div className={styles.cardMeta}>
                  {p.score} point{p.score !== 1 ? "s" : ""} &middot;{" "}
                  {p.comment_count} comment{p.comment_count !== 1 ? "s" : ""}
                </div>
              </Link>
            ))
          )}
        </div>
      )}

      {tab === "comments" && (
        <div className={styles.list}>
          {!comments ? (
            <p className={styles.loading}>Loading...</p>
          ) : comments.items.length === 0 ? (
            <p className={styles.empty}>No comments yet</p>
          ) : (
            comments.items.map((c) => (
              <Link
                key={c.id}
                href={`/c/${c.community_slug}/post/${c.post_id}`}
                className={styles.card}
              >
                <div className={styles.cardTop}>
                  <span className={styles.community}>c/{c.community_slug}</span>
                  <span className={styles.dot}>&middot;</span>
                  <span className={styles.time}>{timeAgo(c.created_at)}</span>
                </div>
                <div className={styles.commentBody}>
                  {stripHtml(c.body_html).slice(0, 180)}
                </div>
                <div className={styles.cardMeta}>
                  on &ldquo;{c.post_title}&rdquo; &middot; {c.score} point
                  {c.score !== 1 ? "s" : ""}
                </div>
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  );
}
