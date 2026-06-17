"use client";

import { useRef, useState } from "react";
import { Avatar } from "@/components/ui/Avatar";
import styles from "./AvatarUpload.module.css";

interface Props {
  currentUrl: string | null;
  displayName: string;
  onUploaded: (url: string) => void;
}

export function AvatarUpload({ currentUrl, displayName, onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const initials = displayName
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError("");

    try {
      const signRes = await fetch("/api/uploads/sign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          content_type: file.type,
        }),
      });
      if (!signRes.ok) {
        const err = await signRes.json();
        throw new Error(err.detail || "Failed to get upload URL");
      }
      const { key, upload_url } = await signRes.json();

      const putRes = await fetch(upload_url, {
        method: "PUT",
        headers: { "Content-Type": file.type },
        body: file,
      });
      if (!putRes.ok) throw new Error("Upload failed");

      const finalRes = await fetch("/api/uploads/finalize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key }),
      });
      if (!finalRes.ok) {
        const err = await finalRes.json();
        throw new Error(err.detail || "Finalize failed");
      }
      const { url } = await finalRes.json();

      const patchRes = await fetch("/api/users/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ avatar_url: url }),
      });
      if (patchRes.ok) {
        onUploaded(url);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className={styles.wrapper}>
      <button
        type="button"
        className={styles.avatarBtn}
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
      >
        <Avatar
          alt={displayName}
          fallback={initials}
          size="lg"
          src={currentUrl ?? undefined}
        />
        <span className={styles.overlay}>
          {uploading ? "Uploading..." : "Change"}
        </span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        className={styles.hidden}
        onChange={handleFile}
      />
      {error && <span className={styles.error}>{error}</span>}
    </div>
  );
}
