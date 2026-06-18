import Link from "next/link";
import { notFound } from "next/navigation";
import { Avatar } from "@/components/ui/Avatar";
import { VoteWidget } from "@/components/VoteWidget";
import { CommentSection } from "./CommentSection";
import { PostActions } from "./PostActions";
import { timeAgo } from "@/lib/text";
import styles from "./PostDetail.module.css";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8001";

interface PostData {
  id: string;
  community_id: string;
  community_slug: string | null;
  community_name: string | null;
  author_id: string | null;
  author_handle: string | null;
  author_display_name: string | null;
  author_avatar_url: string | null;
  title: string;
  body_html: string;
  score: number;
  comment_count: number;
  is_pinned: boolean;
  deleted_at: string | null;
  removed_at: string | null;
  created_at: string;
  updated_at: string;
}

async function getPost(id: string): Promise<PostData | null> {
  const res = await fetch(`${BACKEND_URL}/api/posts/${id}`, {
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

export default async function PostDetailPage({
  params,
}: {
  params: Promise<{ slug: string; id: string }>;
}) {
  const { slug, id } = await params;
  const post = await getPost(id);
  if (!post) notFound();

  const initials = (post.author_display_name ?? "?")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <article className={styles.page}>
      <div className={styles.breadcrumb}>
        <Link href={`/c/${slug}`} className={styles.crumbLink}>
          c/{slug}
        </Link>
      </div>

      {post.removed_at && (
        <div className={styles.removedBanner}>
          This post was removed by a moderator.
        </div>
      )}

      <h1 className={styles.title}>
        {post.is_pinned && <span className={styles.pin}>📌</span>}
        {post.title}
      </h1>

      <div className={styles.authorRow}>
        <Avatar
          alt={post.author_display_name ?? "Unknown"}
          fallback={initials}
          size="sm"
          src={post.author_avatar_url ?? undefined}
        />
        <span className={styles.authorName}>
          {post.author_handle ? (
            <Link
              href={`/u/${post.author_handle}`}
              className={styles.authorLink}
            >
              {post.author_display_name ?? post.author_handle}
            </Link>
          ) : (
            "[deleted]"
          )}
        </span>
        <span className={styles.timestamp}>{timeAgo(post.created_at)}</span>
      </div>

      {!post.removed_at && (
        <div
          className={styles.body}
          dangerouslySetInnerHTML={{ __html: post.body_html }}
        />
      )}

      <div className={styles.stats}>
        <VoteWidget
          targetType="post"
          targetId={post.id}
          score={post.score}
          userVote={0}
          layout="horizontal"
        />
        <span>·</span>
        <span>
          {post.comment_count}{" "}
          {post.comment_count === 1 ? "comment" : "comments"}
        </span>
      </div>

      <PostActions postId={post.id} slug={slug} />

      <CommentSection postId={post.id} />
    </article>
  );
}
