"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { JSONContent } from "@tiptap/react";
import { Button } from "@/components/ui/Button";
import { SyntrixEditor } from "@/lib/editor/SyntrixEditor";
import { AnswerCard } from "./AnswerCard";
import type { AnswerData } from "./AnswerCard";
import styles from "./AnswerSection.module.css";

interface Props {
  postId: string;
  questionAuthorId: string | null;
}

export function AnswerSection({ postId, questionAuthorId }: Props) {
  const [answers, setAnswers] = useState<AnswerData[]>([]);
  const [count, setCount] = useState(0);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const bodyRef = useRef<JSONContent>({ type: "doc", content: [] });
  const [editorKey, setEditorKey] = useState(0);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((u) => {
        if (u) setCurrentUserId(u.id);
      })
      .catch(() => {});
  }, []);

  const fetchAnswers = useCallback(async () => {
    const res = await fetch(`/api/posts/${postId}/answers`);
    if (!res.ok) return;
    const data = await res.json();
    setAnswers(data.answers);
    setCount(data.count);
  }, [postId]);

  useEffect(() => {
    fetchAnswers();
  }, [fetchAnswers]);

  async function handleSubmitAnswer(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch(`/api/posts/${postId}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body_json: bodyRef.current }),
      });
      if (res.ok) {
        bodyRef.current = { type: "doc", content: [] };
        setEditorKey((k) => k + 1);
        await fetchAnswers();
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAccept(answerId: string) {
    const res = await fetch(`/api/answers/${answerId}/accept`, {
      method: "POST",
    });
    if (res.ok) await fetchAnswers();
  }

  async function handleUnaccept(answerId: string) {
    const res = await fetch(`/api/answers/${answerId}/accept`, {
      method: "DELETE",
    });
    if (res.ok) await fetchAnswers();
  }

  function handleUpdate(
    answerId: string,
    html: string,
    json: Record<string, unknown>,
  ) {
    setAnswers((prev) =>
      prev.map((a) =>
        a.id === answerId ? { ...a, body_html: html, body_json: json } : a,
      ),
    );
  }

  function handleDelete(answerId: string) {
    setAnswers((prev) => prev.filter((a) => a.id !== answerId));
    setCount((c) => c - 1);
  }

  const isQuestionAuthor = currentUserId === questionAuthorId;

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>
        {count} {count === 1 ? "Answer" : "Answers"}
      </h2>

      <div className={styles.list}>
        {answers.map((a) => (
          <AnswerCard
            key={a.id}
            answer={a}
            isQuestionAuthor={isQuestionAuthor}
            currentUserId={currentUserId}
            onAccept={handleAccept}
            onUnaccept={handleUnaccept}
            onUpdate={handleUpdate}
            onDelete={handleDelete}
          />
        ))}
      </div>

      {currentUserId && (
        <form onSubmit={handleSubmitAnswer} className={styles.form}>
          <h3 className={styles.formHeading}>Your Answer</h3>
          <SyntrixEditor
            key={editorKey}
            placeholder="Write your answer..."
            onChange={(json) => {
              bodyRef.current = json;
            }}
          />
          <div className={styles.formActions}>
            <Button type="submit" variant="primary" disabled={submitting}>
              {submitting ? "Posting..." : "Post Answer"}
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}
