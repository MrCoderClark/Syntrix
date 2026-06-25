"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import styles from "./CreateRoomModal.module.css";

interface CreateRoomModalProps {
  communityId: string;
  communityName: string;
  onCreated: (room: {
    id: string;
    name: string;
    slug: string;
    is_private: boolean;
    is_default: boolean;
    is_dm: boolean;
    community_id: string | null;
  }) => void;
  onClose: () => void;
}

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80);
}

export function CreateRoomModal({
  communityId,
  communityName,
  onCreated,
  onClose,
}: CreateRoomModalProps) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);
  const [isPrivate, setIsPrivate] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const overlayRef = useRef<HTMLDivElement>(null);

  const handleNameChange = useCallback(
    (val: string) => {
      setName(val);
      if (!slugEdited) setSlug(toSlug(val));
    },
    [slugEdited],
  );

  const handleSubmit = useCallback(async () => {
    if (!name.trim() || submitting) return;
    setSubmitting(true);
    setError("");

    const res = await fetch(`/api/communities/${communityId}/rooms`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name.trim(),
        slug: slug || toSlug(name),
        is_private: isPrivate,
      }),
    });

    if (res.ok) {
      const room = await res.json();
      onCreated(room);
    } else {
      const data = await res.json().catch(() => null);
      setError(data?.detail ?? "Failed to create room");
    }
    setSubmitting(false);
  }, [name, slug, isPrivate, submitting, communityId, onCreated]);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div
      className={styles.overlay}
      ref={overlayRef}
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className={styles.modal}>
        <h3 className={styles.title}>New room in {communityName}</h3>

        <label className={styles.label}>Name</label>
        <Input
          value={name}
          onChange={(e) => handleNameChange(e.target.value)}
          placeholder="general-chat"
          autoFocus
        />

        <label className={styles.label}>Slug</label>
        <Input
          value={slug}
          onChange={(e) => {
            setSlug(e.target.value);
            setSlugEdited(true);
          }}
          placeholder="general-chat"
        />

        <label className={styles.checkLabel}>
          <input
            type="checkbox"
            checked={isPrivate}
            onChange={(e) => setIsPrivate(e.target.checked)}
          />
          Private room
        </label>

        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.actions}>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={!name.trim() || submitting}
          >
            {submitting ? "Creating..." : "Create Room"}
          </Button>
        </div>
      </div>
    </div>
  );
}
