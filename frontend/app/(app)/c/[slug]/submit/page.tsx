"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState, useCallback } from "react";
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

interface SimilarQuestion {
  id: string;
  title: string;
  score: number;
  answer_count: number;
  has_accepted_answer: boolean;
  similarity: number;
}

function extractText(node: JSONContent): string {
  if (node.type === "text") return node.text ?? "";
  return (node.content ?? []).map(extractText).join(" ");
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

  const [suggestions, setSuggestions] = useState<SimilarQuestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [modalMatches, setModalMatches] = useState<SimilarQuestion[]>([]);
  const [showModal, setShowModal] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetch(`/api/communities/${params.slug}`)
      .then((r) => r.json())
      .then((c) => setCommunityId(c.id))
      .catch(() => {});
  }, [params.slug]);

  const fetchTitleSuggestions = useCallback(
    async (query: string) => {
      if (query.length < 10 || postType !== "question") {
        setSuggestions([]);
        setShowSuggestions(false);
        return;
      }
      try {
        const resp = await fetch(
          `/api/communities/${params.slug}/questions/similar?title=${encodeURIComponent(query)}`,
        );
        if (resp.ok) {
          const data = await resp.json();
          setSuggestions(data.items);
          setShowSuggestions(data.items.length > 0);
        }
      } catch {
        /* ignore network errors for suggestions */
      }
    },
    [params.slug, postType],
  );

  function handleTitleChange(value: string) {
    setTitle(value.slice(0, 300));
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchTitleSuggestions(value), 300);
  }

  async function doSubmit() {
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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!communityId || !title.trim()) return;

    if (postType === "question") {
      try {
        const bodyText = extractText(bodyRef.current);
        const resp = await fetch(
          `/api/communities/${params.slug}/questions/similar`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: title.trim(), body_text: bodyText }),
          },
        );
        if (resp.ok) {
          const data = await resp.json();
          if (data.items.length > 0) {
            setModalMatches(data.items);
            setShowModal(true);
            return;
          }
        }
      } catch {
        /* if similarity check fails, just submit */
      }
    }

    await doSubmit();
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
          onClick={() => {
            setPostType("discussion");
            setSuggestions([]);
            setShowSuggestions(false);
          }}
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
        <div className={`${styles.titleField} ${styles.suggestionsWrap}`}>
          <input
            className={styles.titleInput}
            placeholder={isQuestion ? "What's your question?" : "Post title"}
            value={title}
            onChange={(e) => handleTitleChange(e.target.value)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            maxLength={300}
            required
          />
          <span className={styles.counter}>{title.length}/300</span>

          {showSuggestions && suggestions.length > 0 && (
            <div className={styles.suggestionsPanel}>
              <div className={styles.suggestionsHeader}>Similar questions</div>
              {suggestions.map((q) => (
                <a
                  key={q.id}
                  href={`/c/${params.slug}/post/${q.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.suggestionItem}
                >
                  <span className={styles.suggestionTitle}>{q.title}</span>
                  <span className={styles.suggestionMeta}>
                    <span>{q.score} votes</span>
                    <span>{q.answer_count} answers</span>
                    {q.has_accepted_answer && (
                      <span className={styles.suggestionAccepted}>
                        &#10003;
                      </span>
                    )}
                  </span>
                </a>
              ))}
            </div>
          )}
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

      {showModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <h2 className={styles.modalTitle}>
              Similar questions already exist
            </h2>
            <p className={styles.modalDesc}>
              Check if any of these answer your question before posting:
            </p>
            <div className={styles.modalList}>
              {modalMatches.map((q) => (
                <a
                  key={q.id}
                  href={`/c/${params.slug}/post/${q.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.suggestionItem}
                >
                  <span className={styles.suggestionTitle}>{q.title}</span>
                  <span className={styles.suggestionMeta}>
                    <span>{q.score} votes</span>
                    <span>{q.answer_count} answers</span>
                    {q.has_accepted_answer && (
                      <span className={styles.suggestionAccepted}>
                        &#10003;
                      </span>
                    )}
                  </span>
                </a>
              ))}
            </div>
            <div className={styles.modalActions}>
              <Button variant="secondary" onClick={() => setShowModal(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  setShowModal(false);
                  doSubmit();
                }}
              >
                Post anyway
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
