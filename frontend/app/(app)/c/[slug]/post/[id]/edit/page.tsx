"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { JSONContent } from "@tiptap/react";
import { Button } from "@/components/ui/Button";
import { SyntrixEditor } from "@/lib/editor/SyntrixEditor";
import styles from "../../submit/Submit.module.css";

interface PostData {
  id: string;
  title: string;
  body_json: JSONContent;
}

export default function EditPostPage() {
  const params = useParams<{ slug: string; id: string }>();
  const router = useRouter();
  const [post, setPost] = useState<PostData | null>(null);
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const bodyRef = useRef<JSONContent>({ type: "doc", content: [] });

  useEffect(() => {
    fetch(`/api/posts/${params.id}`)
      .then((r) => r.json())
      .then((data) => {
        setPost(data);
        setTitle(data.title);
        bodyRef.current = data.body_json;
      })
      .catch(() => {});
  }, [params.id]);

  if (!post) return <p style={{ padding: "32px" }}>Loading...</p>;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("saving");
    setErrorMsg("");

    const res = await fetch(`/api/posts/${params.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title.trim(),
        body_json: bodyRef.current,
      }),
    });

    if (res.ok) {
      router.push(`/c/${params.slug}/post/${params.id}`);
    } else {
      const err = await res.json();
      setErrorMsg(err.detail || "Failed to update");
      setStatus("error");
    }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Edit post</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.titleField}>
          <input
            className={styles.titleInput}
            value={title}
            onChange={(e) => setTitle(e.target.value.slice(0, 300))}
            maxLength={300}
            required
          />
          <span className={styles.counter}>{title.length}/300</span>
        </div>
        <SyntrixEditor
          initialContent={post.body_json}
          onChange={(json) => {
            bodyRef.current = json;
          }}
        />
        <div className={styles.actions}>
          <Button
            type="submit"
            variant="primary"
            disabled={status === "saving" || !title.trim()}
          >
            {status === "saving" ? "Saving..." : "Save changes"}
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => router.push(`/c/${params.slug}/post/${params.id}`)}
          >
            Cancel
          </Button>
          {status === "error" && (
            <span className={styles.error}>{errorMsg}</span>
          )}
        </div>
      </form>
    </div>
  );
}
