"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { JSONContent } from "@tiptap/react";
import { Button } from "@/components/ui/Button";
import { TagPicker } from "@/components/ui/TagPicker";
import { SyntrixEditor } from "@/lib/editor/SyntrixEditor";
import styles from "./Submit.module.css";

type PostType = "discussion" | "question";

interface TagOption {
  id: string;
  slug: string;
  name: string;
  color: string | null;
  usage_count: number;
}

export default function SubmitPostPage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [postType, setPostType] = useState<PostType>("discussion");
  const [selectedTags, setSelectedTags] = useState<TagOption[]>([]);
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
        post_type: postType,
        tag_ids: postType === "question" ? selectedTags.map((t) => t.id) : [],
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

  const isQuestion = postType === "question";

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>
        {isQuestion ? "Ask a question" : "New post"} in{" "}
        <span className={styles.community}>c/{params.slug}</span>
      </h1>

      <div className={styles.typeTabs}>
        <button
          type="button"
          className={`${styles.typeTab} ${!isQuestion ? styles.typeTabActive : ""}`}
          onClick={() => setPostType("discussion")}
        >
          Post
        </button>
        <button
          type="button"
          className={`${styles.typeTab} ${isQuestion ? styles.typeTabActive : ""}`}
          onClick={() => setPostType("question")}
        >
          Question
        </button>
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.titleField}>
          <input
            className={styles.titleInput}
            placeholder={isQuestion ? "What's your question?" : "Post title"}
            value={title}
            onChange={(e) => setTitle(e.target.value.slice(0, 300))}
            maxLength={300}
            required
          />
          <span className={styles.counter}>{title.length}/300</span>
        </div>

        {isQuestion && (
          <TagPicker
            communitySlug={params.slug}
            selected={selectedTags}
            onChange={setSelectedTags}
          />
        )}

        <SyntrixEditor
          placeholder={
            isQuestion
              ? "Describe your question in detail..."
              : "What's on your mind?"
          }
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
            {status === "submitting"
              ? isQuestion
                ? "Asking..."
                : "Posting..."
              : isQuestion
                ? "Ask"
                : "Post"}
          </Button>
          {status === "error" && (
            <span className={styles.error}>{errorMsg}</span>
          )}
        </div>
      </form>
    </div>
  );
}
