import Link from "next/link";
import { notFound } from "next/navigation";
import { Avatar } from "@/components/ui/Avatar";
import { PageHeader, TitleAccent } from "@/components/ui/PageHeader";
import { JoinButton } from "./JoinButton";
import styles from "./page.module.css";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8001";

interface CommunityDetail {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  color: string;
  owner_id: string;
  member_count: number;
  created_at: string;
  is_member: boolean;
  membership_role: string | null;
  is_banned: boolean;
}

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

async function getCommunity(slug: string): Promise<CommunityDetail | null> {
  const res = await fetch(`${BACKEND_URL}/api/communities/${slug}`, {
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

async function getPosts(communityId: string): Promise<PostItem[]> {
  const res = await fetch(`${BACKEND_URL}/api/posts/community/${communityId}`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.posts ?? [];
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

export default async function CommunityPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const community = await getCommunity(slug);

  if (!community) notFound();

  const posts = await getPosts(community.id);

  return (
    <div
      style={{ "--community-color": community.color } as React.CSSProperties}
    >
      <PageHeader
        glyph={community.name[0].toUpperCase()}
        glyphStyle={{
          background: community.color,
          boxShadow: `6px 6px 0 ${community.color}33`,
        }}
        eyebrow={`c/${community.slug}`}
        title={
          <>
            {community.name.split(" ").slice(0, -1).join(" ")}{" "}
            <TitleAccent>{community.name.split(" ").slice(-1)[0]}</TitleAccent>
          </>
        }
        subtitle={community.description ?? undefined}
        actions={
          <div className={styles.headerActions}>
            <JoinButton slug={community.slug} />
            <Link href={`/c/${slug}/submit`} className={styles.newPostBtn}>
              New Post
            </Link>
          </div>
        }
      />

      <div className={styles.meta}>
        <div className={styles.stat}>
          <span className={styles.statValue}>{community.member_count}</span>
          <span className={styles.statLabel}>
            {community.member_count === 1 ? "member" : "members"}
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>
            {new Date(community.created_at).toLocaleDateString("en-US", {
              month: "short",
              year: "numeric",
            })}
          </span>
          <span className={styles.statLabel}>created</span>
        </div>
      </div>

      <div className={styles.content}>
        {posts.length === 0 ? (
          <p className={styles.placeholder}>
            No posts yet in c/{community.slug}. Be the first to post!
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
                <Link
                  key={post.id}
                  href={`/c/${slug}/post/${post.id}`}
                  className={styles.postCard}
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
                      {post.score} pts · {post.comment_count} comments
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
