import { Avatar } from "@/components/ui/Avatar";
import styles from "./page.module.css";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8001";

async function getProfile(handle: string) {
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

  return (
    <div className={styles.profile}>
      <div className={styles.top}>
        <Avatar alt={profile.display_name} fallback={initials} size="lg" />
        <div className={styles.info}>
          <h1 className={styles.displayName}>{profile.display_name}</h1>
          <div className={styles.handle}>u/{profile.handle}</div>
          {profile.audience_tag && (
            <span className={styles.tag}>{profile.audience_tag}</span>
          )}
        </div>
      </div>
      {profile.bio && <p className={styles.bio}>{profile.bio}</p>}
      <div className={styles.joined}>
        Joined{" "}
        {new Date(profile.created_at).toLocaleDateString("en-US", {
          month: "long",
          year: "numeric",
        })}
      </div>
    </div>
  );
}
