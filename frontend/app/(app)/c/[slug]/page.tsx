import Link from "next/link";
import { notFound } from "next/navigation";
import { PageHeader, TitleAccent } from "@/components/ui/PageHeader";
import { TagPill } from "@/components/ui/TagPill";
import { CommunityFeed } from "./CommunityFeed";
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

interface TagBrief {
  id: string;
  slug: string;
  name: string;
  color: string | null;
}

async function getCommunity(slug: string): Promise<CommunityDetail | null> {
  const res = await fetch(`${BACKEND_URL}/api/communities/${slug}`, {
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

async function getTags(slug: string): Promise<TagBrief[]> {
  const res = await fetch(`${BACKEND_URL}/api/communities/${slug}/tags`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return res.json();
}

export default async function CommunityPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const [community, tags] = await Promise.all([
    getCommunity(slug),
    getTags(slug),
  ]);

  if (!community) notFound();

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

      {tags.length > 0 && (
        <div className={styles.tagsRow}>
          {tags.map((t) => (
            <TagPill key={t.id} name={t.name} color={t.color} />
          ))}
        </div>
      )}

      <div className={styles.content}>
        <CommunityFeed communityId={community.id} slug={slug} />
      </div>
    </div>
  );
}
