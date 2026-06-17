"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { JSONContent } from "@tiptap/react";
import { Button } from "@/components/ui/Button";
import { SyntrixEditor } from "@/lib/editor/SyntrixEditor";
import styles from "./Submit.module.css";

export default function SubmitPostPage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const bodyRef = useRef<JSONContent>({ type: "doc", content: [] });
  const [communityId, setCommunityId] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/communities/${params.slug}`)
      .then((r) => r.json())
      .then((c) => setCommunityId(c.id))
      .catch(() => {});
  }, [params.slug]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!communityId || !title.trim()) return;

    setStatus("submitting");
    setErrorMsg("");

    const res = await fetch("/api/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        community_id: communityId,
        title: title.trim(),
        body_json: bodyRef.current,
      }),
    });

    if (res.ok) {
      const post = await res.json();
      router.push(`/c/${params.slug}/post/${post.id}`);
    } else {
      const err = await res.json();
      setErrorMsg(err.detail || "Failed to create post");
      setStatus("error");
    }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>
        New post in <span className={styles.community}>c/{params.slug}</span>
      </h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.titleField}>
          <input
            className={styles.titleInput}
            placeholder="Post title"
            value={title}
            onChange={(e) => setTitle(e.target.value.slice(0, 300))}
            maxLength={300}
            required
          />
          <span className={styles.counter}>{title.length}/300</span>
        </div>
        <SyntrixEditor
          placeholder="What's on your mind?"
          onChange={(json) => {
            bodyRef.current = json;
          }}
        />
        <div className={styles.actions}>
          <Button
            type="submit"
            variant="primary"
            disabled={status === "submitting" || !title.trim()}
          >
            {status === "submitting" ? "Posting..." : "Post"}
          </Button>
          {status === "error" && (
            <span className={styles.error}>{errorMsg}</span>
          )}
        </div>
      </form>
    </div>
  );
}
