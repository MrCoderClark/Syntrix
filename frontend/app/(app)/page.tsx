"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Avatar } from "@/components/ui/Avatar";
import { FeedControls } from "@/components/FeedControls";
import { PostCardSkeleton } from "@/components/PostCardSkeleton";
import { VoteWidget } from "@/components/VoteWidget";
import { stripHtml, timeAgo } from "@/lib/text";
import styles from "./Home.module.css";

interface PostItem {
  id: string;
  community_id: string;
  community_slug: string | null;
  community_name: string | null;
  title: string;
  author_handle: string | null;
  author_display_name: string | null;
  author_avatar_url: string | null;
  score: number;
  comment_count: number;
  is_pinned: boolean;
  removed_at: string | null;
  created_at: string;
  body_html: string;
}

type SortMode = "hot" | "new" | "top";
type Period = "today" | "week" | "month" | "all";

export default function HomePage() {
  const [sort, setSort] = useState<SortMode>("hot");
  const [period, setPeriod] = useState<Period>("all");
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [postVotes, setPostVotes] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  async function fetchPostVotes(postIds: string[]) {
    if (postIds.length === 0) return;
    const params = new URLSearchParams({
      target_type: "post",
      target_ids: postIds.join(","),
    });
    try {
      const res = await fetch(`/api/votes/mine?${params}`);
      if (res.ok) {
        const data = await res.json();
        setPostVotes(data.votes ?? {});
      }
    } catch {
      /* ignore — votes default to 0 */
    }
  }

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const params = new URLSearchParams({ sort });
      if (sort === "top" && period !== "all") params.set("period", period);
      const res = await fetch(`/api/feed?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        const fetchedPosts = data.posts ?? [];
        setPosts(fetchedPosts);
        await fetchPostVotes(fetchedPosts.map((p: PostItem) => p.id));
      } else {
        setError(true);
      }
    } catch {
      setError(true);
    }
    setLoading(false);
  }, [sort, period]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Your Feed</h1>

      <FeedControls
        sort={sort}
        period={period}
        onSortChange={setSort}
        onPeriodChange={setPeriod}
      />

      {loading ? (
        <PostCardSkeleton />
      ) : error ? (
        <div className={styles.empty}>
          <p>Something went wrong loading your feed.</p>
          <button onClick={fetchPosts} className={styles.exploreLink}>
            Try again
          </button>
        </div>
      ) : posts.length === 0 ? (
        <div className={styles.empty}>
          <p>No posts in your feed yet.</p>
          <Link href="/communities" className={styles.exploreLink}>
            Join some communities to get started
          </Link>
        </div>
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
                    userVote={postVotes[post.id] ?? 0}
                  />
                </div>
                <Link
                  href={`/c/${post.community_slug}/post/${post.id}`}
                  className={styles.postContent}
                >
                  <div className={styles.postHeader}>
                    {post.community_slug && (
                      <span className={styles.communityTag}>
                        c/{post.community_slug}
                      </span>
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
                      src={post.author_avatar_url ?? undefined}
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
                      {post.comment_count} comments
                    </span>
                  </div>
                </Link>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
