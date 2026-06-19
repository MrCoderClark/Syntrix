import Link from "next/link";
import { Avatar } from "@/components/ui/Avatar";
import { GitHubIcon, DiscordIcon, GlobeIcon } from "@/components/icons";
import { ProfileTabs } from "./ProfileTabs";
import styles from "./page.module.css";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8001";

interface CommunityBrief {
  slug: string;
  name: string;
  color: string;
}

interface ProfileBadge {
  slug: string;
  name: string;
  icon: string | null;
  tier: string;
  awarded_at: string;
}

interface Profile {
  id: string;
  handle: string;
  display_name: string;
  avatar_url: string | null;
  bio: string | null;
  audience_tag: string | null;
  role: string;
  github_username: string | null;
  discord_username: string | null;
  website_url: string | null;
  post_count: number;
  comment_count: number;
  karma: number;
  reputation: number;
  badges: ProfileBadge[];
  communities: CommunityBrief[];
  created_at: string;
}

async function getProfile(handle: string): Promise<Profile | null> {
  const res = await fetch(`${BACKEND_URL}/api/users/${handle}`, {
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

export default async function ProfilePage({
  params,
}: {
  params: Promise<{ handle: string }>;
}) {
  const { handle } = await params;
  const profile = await getProfile(handle);

  if (!profile) {
    return (
      <div className={styles.profile}>
        <p>User not found.</p>
      </div>
    );
  }

  const initials = profile.display_name
    .split(" ")
    .map((w: string) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const hasSocial =
    profile.github_username || profile.discord_username || profile.website_url;

  return (
    <div className={styles.profile}>
      <div className={styles.header}>
        <Avatar
          src={profile.avatar_url ?? undefined}
          alt={profile.display_name}
          fallback={initials}
          size="xl"
        />
        <div className={styles.headerInfo}>
          <h1 className={styles.displayName}>{profile.display_name}</h1>
          <div className={styles.handleRow}>
            <span className={styles.handle}>u/{profile.handle}</span>
            {profile.audience_tag && (
              <span className={styles.tag}>{profile.audience_tag}</span>
            )}
          </div>
          {profile.bio && <p className={styles.bio}>{profile.bio}</p>}
        </div>
      </div>

      <div className={styles.statsRow}>
        <div className={styles.stat}>
          <span className={styles.statValue}>{profile.post_count}</span>
          <span className={styles.statLabel}>Posts</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{profile.comment_count}</span>
          <span className={styles.statLabel}>Comments</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{profile.karma}</span>
          <span className={styles.statLabel}>Karma</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{profile.reputation}</span>
          <span className={styles.statLabel}>Reputation</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{profile.communities.length}</span>
          <span className={styles.statLabel}>Communities</span>
        </div>
      </div>

      {profile.badges.length > 0 && (
        <div className={styles.badgeRow}>
          {profile.badges.map((b) => (
            <span
              key={b.slug}
              className={`${styles.badge} ${styles[`badge_${b.tier}`]}`}
              title={b.name}
            >
              {b.icon && <span className={styles.badgeIcon}>{b.icon}</span>}
              {b.name}
            </span>
          ))}
        </div>
      )}

      <div className={styles.meta}>
        {hasSocial && (
          <div className={styles.socialRow}>
            {profile.github_username && (
              <a
                href={`https://github.com/${profile.github_username}`}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.socialLink}
              >
                <GitHubIcon size={15} />
                {profile.github_username}
              </a>
            )}
            {profile.discord_username && (
              <span className={styles.socialTag}>
                <DiscordIcon size={15} />
                {profile.discord_username}
              </span>
            )}
            {profile.website_url && (
              <a
                href={profile.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.socialLink}
              >
                <GlobeIcon size={15} />
                {profile.website_url.replace(/^https?:\/\//, "")}
              </a>
            )}
          </div>
        )}

        <div className={styles.infoRow}>
          <span className={styles.joined}>
            Joined{" "}
            {new Date(profile.created_at).toLocaleDateString("en-US", {
              month: "long",
              year: "numeric",
            })}
          </span>
          {profile.communities.length > 0 && (
            <span className={styles.dot}>&middot;</span>
          )}
          <div className={styles.communityTags}>
            {profile.communities.map((c) => (
              <Link
                key={c.slug}
                href={`/c/${c.slug}`}
                className={styles.communityTag}
              >
                <span
                  className={styles.communityDot}
                  style={{ background: c.color }}
                />
                {c.name}
              </Link>
            ))}
          </div>
        </div>
      </div>

      <ProfileTabs handle={profile.handle} />
    </div>
  );
}
