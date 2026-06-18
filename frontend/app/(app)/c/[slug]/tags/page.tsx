"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { TagPill } from "@/components/ui/TagPill";
import styles from "./page.module.css";

interface Tag {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  color: string | null;
  usage_count: number;
}

interface UserInfo {
  role: string;
}

export default function TagsPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;

  const [tags, setTags] = useState<Tag[]>([]);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [color, setColor] = useState("#1e3a5f");
  const [status, setStatus] = useState<"idle" | "saving" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editColor, setEditColor] = useState("");

  useEffect(() => {
    fetch(`/api/communities/${slug}/tags`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setTags)
      .catch(() => setTags([]));
    fetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then(setUser)
      .catch(() => setUser(null));
  }, [slug]);

  const canManage = user?.role === "admin";

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setStatus("saving");
    setErrorMsg("");
    const res = await fetch(`/api/communities/${slug}/tags`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        description: description || null,
        color: color || null,
      }),
    });
    if (res.ok) {
      const tag = await res.json();
      setTags((prev) =>
        [...prev, tag].sort((a, b) => a.name.localeCompare(b.name)),
      );
      setName("");
      setDescription("");
      setColor("#1e3a5f");
      setStatus("idle");
    } else {
      const err = await res.json();
      setErrorMsg(err.detail || "Failed to create tag");
      setStatus("error");
    }
  }

  async function handleUpdate(tagSlug: string) {
    const res = await fetch(`/api/communities/${slug}/tags/${tagSlug}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: editName || undefined,
        description: editDesc,
        color: editColor || undefined,
      }),
    });
    if (res.ok) {
      const updated = await res.json();
      setTags((prev) =>
        prev
          .map((t) => (t.id === editingId ? { ...updated } : t))
          .sort((a: Tag, b: Tag) => a.name.localeCompare(b.name)),
      );
      setEditingId(null);
    }
  }

  async function handleDelete(tag: Tag) {
    if (tag.usage_count > 0) return;
    const res = await fetch(`/api/communities/${slug}/tags/${tag.slug}`, {
      method: "DELETE",
    });
    if (res.ok) {
      setTags((prev) => prev.filter((t) => t.id !== tag.id));
    }
  }

  function startEdit(tag: Tag) {
    setEditingId(tag.id);
    setEditName(tag.name);
    setEditDesc(tag.description ?? "");
    setEditColor(tag.color ?? "#1e3a5f");
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Tags</h1>
      <p className={styles.subtitle}>
        Tags help organize questions within this community.
      </p>

      {tags.length === 0 ? (
        <p className={styles.empty}>No tags yet</p>
      ) : (
        <div className={styles.tagList}>
          {tags.map((tag) =>
            editingId === tag.id ? (
              <div key={tag.id} className={styles.editRow}>
                <input
                  className={styles.editInput}
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="Name"
                />
                <input
                  className={styles.editInput}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  placeholder="Description"
                />
                <input
                  type="color"
                  className={styles.colorInput}
                  value={editColor}
                  onChange={(e) => setEditColor(e.target.value)}
                />
                <button
                  className={styles.saveBtn}
                  onClick={() => handleUpdate(tag.slug)}
                >
                  Save
                </button>
                <button
                  className={styles.cancelBtn}
                  onClick={() => setEditingId(null)}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div key={tag.id} className={styles.tagRow}>
                <TagPill name={tag.name} color={tag.color} />
                {tag.description && (
                  <span className={styles.tagDesc}>{tag.description}</span>
                )}
                <span className={styles.tagCount}>
                  {tag.usage_count} question{tag.usage_count !== 1 ? "s" : ""}
                </span>
                {canManage && (
                  <div className={styles.tagActions}>
                    <button
                      className={styles.editBtn}
                      onClick={() => startEdit(tag)}
                    >
                      Edit
                    </button>
                    {tag.usage_count === 0 && (
                      <button
                        className={styles.deleteBtn}
                        onClick={() => handleDelete(tag)}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                )}
              </div>
            ),
          )}
        </div>
      )}

      {canManage && (
        <>
          <h2 className={styles.sectionTitle}>Create tag</h2>
          <form className={styles.createForm} onSubmit={handleCreate}>
            <div className={styles.formRow}>
              <input
                className={styles.formInput}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Tag name"
                required
                maxLength={50}
              />
              <input
                type="color"
                className={styles.colorInput}
                value={color}
                onChange={(e) => setColor(e.target.value)}
              />
            </div>
            <input
              className={styles.formInput}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description (optional)"
              maxLength={200}
            />
            <button
              type="submit"
              className={styles.createBtn}
              disabled={status === "saving" || !name.trim()}
            >
              {status === "saving" ? "Creating..." : "Create tag"}
            </button>
            {status === "error" && (
              <span className={styles.error}>{errorMsg}</span>
            )}
          </form>
        </>
      )}
    </div>
  );
}
