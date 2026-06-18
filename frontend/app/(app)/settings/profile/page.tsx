"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { AvatarUpload } from "./AvatarUpload";
import styles from "./page.module.css";

interface Profile {
  handle: string;
  display_name: string;
  bio: string | null;
  audience_tag: string | null;
  avatar_url: string | null;
  github_username: string | null;
  discord_username: string | null;
  website_url: string | null;
}

export default function ProfileSettingsPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">(
    "idle",
  );
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => setProfile(data))
      .catch(() => setProfile(null));
  }, []);

  if (!profile)
    return (
      <p style={{ color: "var(--ink-faint)", padding: "32px 0" }}>
        Loading profile...
      </p>
    );

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!profile) return;
    setStatus("saving");
    setErrorMsg("");
    const res = await fetch("/api/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (res.ok) {
      const updated = await res.json();
      setProfile(updated);
      setStatus("saved");
    } else {
      const err = await res.json();
      setErrorMsg(err.detail || "Failed to save");
      setStatus("error");
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <AvatarUpload
        currentUrl={profile.avatar_url}
        displayName={profile.display_name}
        onUploaded={(url) => setProfile({ ...profile, avatar_url: url })}
      />

      <div className={styles.field}>
        <label className={styles.label}>Handle</label>
        <input
          className={styles.textInput}
          value={profile.handle}
          onChange={(e) => setProfile({ ...profile, handle: e.target.value })}
          maxLength={24}
        />
        <span className={styles.hint}>
          3–24 chars, letters, numbers, underscores
        </span>
      </div>

      <div className={styles.field}>
        <label className={styles.label}>Display name</label>
        <input
          className={styles.textInput}
          value={profile.display_name}
          onChange={(e) =>
            setProfile({ ...profile, display_name: e.target.value })
          }
          maxLength={100}
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label}>Bio</label>
        <textarea
          className={styles.textarea}
          value={profile.bio ?? ""}
          onChange={(e) =>
            setProfile({ ...profile, bio: e.target.value || null })
          }
          maxLength={500}
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label}>I identify as</label>
        <select
          className={styles.select}
          value={profile.audience_tag ?? ""}
          onChange={(e) =>
            setProfile({ ...profile, audience_tag: e.target.value || null })
          }
        >
          <option value="">Prefer not to say</option>
          <option value="gamer">Gamer</option>
          <option value="it">IT Admin</option>
          <option value="dev">Developer</option>
        </select>
      </div>

      <div className={styles.divider} />

      <h3 className={styles.sectionTitle}>Social links</h3>

      <div className={styles.field}>
        <label className={styles.label}>GitHub username</label>
        <input
          className={styles.textInput}
          value={profile.github_username ?? ""}
          onChange={(e) =>
            setProfile({
              ...profile,
              github_username: e.target.value || null,
            })
          }
          placeholder="octocat"
          maxLength={39}
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label}>Discord username</label>
        <input
          className={styles.textInput}
          value={profile.discord_username ?? ""}
          onChange={(e) =>
            setProfile({
              ...profile,
              discord_username: e.target.value || null,
            })
          }
          placeholder="username#1234"
          maxLength={37}
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label}>Website</label>
        <input
          className={styles.textInput}
          value={profile.website_url ?? ""}
          onChange={(e) =>
            setProfile({ ...profile, website_url: e.target.value || null })
          }
          placeholder="https://example.com"
          maxLength={200}
        />
        <span className={styles.hint}>Must start with https://</span>
      </div>

      <div className={styles.actions}>
        <Button type="submit" variant="primary" disabled={status === "saving"}>
          {status === "saving" ? "Saving..." : "Save changes"}
        </Button>
        {status === "saved" && <span className={styles.success}>Saved</span>}
        {status === "error" && <span className={styles.error}>{errorMsg}</span>}
      </div>
    </form>
  );
}
