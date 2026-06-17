"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Avatar } from "@/components/ui/Avatar";
import { FeedControls } from "@/components/FeedControls";
import { VoteWidget } from "@/components/VoteWidget";
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
  removed_at: string | null;
  created_at: string;
  body_html: string;
}

type SortMode = "hot" | "new" | "top";
type Period = "today" | "week" | "month" | "all";

interface Props {
  communityId: string;
  slug: string;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, "").slice(0, 200);
}

export function CommunityFeed({ communityId, slug }: Props) {
  const [sort, setSort] = useState<SortMode>("hot");
  const [period, setPeriod] = useState<Period>("all");
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ sort });
    if (sort === "top" && period !== "all") params.set("period", period);
    const res = await fetch(
      `/api/communities/${communityId}/feed?${params.toString()}`,
    );
    if (res.ok) {
      const data = await res.json();
      setPosts(data.posts ?? []);
    }
    setLoading(false);
  }, [communityId, sort, period]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  return (
    <>
      <FeedControls
        sort={sort}
        period={period}
        onSortChange={setSort}
        onPeriodChange={setPeriod}
      />

      {loading ? (
        <p className={styles.placeholder}>Loading...</p>
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
                      {post.comment_count} comments
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
