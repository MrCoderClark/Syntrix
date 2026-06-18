"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Avatar } from "@/components/ui/Avatar";
import { FeedControls } from "@/components/FeedControls";
import { PostCardSkeleton } from "@/components/PostCardSkeleton";
import { VoteWidget } from "@/components/VoteWidget";
import { stripHtml, timeAgo } from "@/lib/text";
import styles from "./page.module.css";

interface PostItem {
  id: string;
  title: string;
  author_handle: string | null;
  author_display_name: string | null;
  author_avatar_url: string | null;
  score: number;
  comment_count: number;
  is_pinned: boolean;
  post_type: string;
  answer_count: number;
  has_accepted_answer: boolean;
  removed_at: string | null;
  created_at: string;
  body_html: string;
}

type PostTypeFilter = "all" | "discussion" | "question";

type SortMode = "hot" | "new" | "top";
type Period = "today" | "week" | "month" | "all";

interface Props {
  communityId: string;
  slug: string;
}

export function CommunityFeed({ communityId, slug }: Props) {
  const [sort, setSort] = useState<SortMode>("hot");
  const [period, setPeriod] = useState<Period>("all");
  const [typeFilter, setTypeFilter] = useState<PostTypeFilter>("all");
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const params = new URLSearchParams({ sort });
      if (sort === "top" && period !== "all") params.set("period", period);
      if (typeFilter !== "all") params.set("post_type", typeFilter);
      const res = await fetch(
        `/api/communities/${communityId}/feed?${params.toString()}`,
      );
      if (res.ok) {
        const data = await res.json();
        setPosts(data.posts ?? []);
      } else {
        setError(true);
      }
    } catch {
      setError(true);
    }
    setLoading(false);
  }, [communityId, sort, period, typeFilter]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  return (
    <>
      <div className={styles.typeTabs}>
        {(["all", "discussion", "question"] as PostTypeFilter[]).map((t) => (
          <button
            key={t}
            type="button"
            className={`${styles.typeTab} ${typeFilter === t ? styles.typeTabActive : ""}`}
            onClick={() => setTypeFilter(t)}
          >
            {t === "all" ? "All" : t === "discussion" ? "Posts" : "Questions"}
          </button>
        ))}
      </div>

      <FeedControls
        sort={sort}
        period={period}
        onSortChange={setSort}
        onPeriodChange={setPeriod}
      />

      {loading ? (
        <PostCardSkeleton />
      ) : error ? (
        <div className={styles.placeholder}>
          Something went wrong loading posts.{" "}
          <button
            onClick={fetchPosts}
            style={{
              color: "var(--accent)",
              textDecoration: "underline",
              background: "none",
              border: "none",
              cursor: "pointer",
              font: "inherit",
            }}
          >
            Try again
          </button>
        </div>
      ) : posts.length === 0 ? (
        <p className={styles.placeholder}>
          No posts yet in c/{slug}. Be the first to post!
        </p>
      ) : (
        <div className={styles.feed}>
          {posts.map((post) => {
            const initials = (post.author_display_name ?? "?")
              .split(" ")
              .map((w) => w[0])
              .join("")
              .slice(0, 2)
              .toUpperCase();
            return (
              <div key={post.id} className={styles.postCard}>
                <div className={styles.voteCol}>
                  <VoteWidget
                    targetType="post"
                    targetId={post.id}
                    score={post.score}
                    userVote={0}
                  />
                </div>
                <Link
                  href={`/c/${slug}/post/${post.id}`}
                  className={styles.postContent}
                >
                  <div className={styles.postHeader}>
                    {post.is_pinned && (
                      <span className={styles.pinBadge}>pinned</span>
                    )}
                    <h3 className={styles.postTitle}>{post.title}</h3>
                  </div>
                  <p className={styles.postPreview}>
                    {post.removed_at
                      ? "[removed by moderator]"
                      : stripHtml(post.body_html)}
                  </p>
                  <div className={styles.postMeta}>
                    <Avatar
                      alt={post.author_display_name ?? "Unknown"}
                      fallback={initials}
                      size="sm"
                    />
                    <span className={styles.postAuthor}>
                      {post.author_handle ?? "[deleted]"}
                    </span>
                    <span className={styles.postTime}>
                      {timeAgo(post.created_at)}
                    </span>
                    <span className={styles.postStats}>
                      {post.post_type === "question" ? (
                        <>
                          {post.answer_count}{" "}
                          {post.answer_count === 1 ? "answer" : "answers"}
                          {post.has_accepted_answer && (
                            <span className={styles.acceptedMark}> ✓</span>
                          )}
                        </>
                      ) : (
                        <>{post.comment_count} comments</>
                      )}
                    </span>
                  </div>
                </Link>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
