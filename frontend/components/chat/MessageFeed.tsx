"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { timeAgo } from "@/lib/text";
import styles from "./MessageFeed.module.css";

export interface Message {
  id: string;
  room_id: string;
  author_id: string | null;
  author_handle: string | null;
  author_display_name: string | null;
  author_avatar_url: string | null;
  body_json: object | null;
  body_html: string;
  edited_at: string | null;
  deleted_at: string | null;
  created_at: string;
}

interface MessageFeedProps {
  roomId: string;
  typingUsers?: string[];
}

export function MessageFeed({ roomId, typingUsers = [] }: MessageFeedProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const loadMessages = useCallback(
    async (before?: string) => {
      const params = new URLSearchParams();
      if (before) params.set("before", before);
      params.set("limit", "50");

      const res = await fetch(`/api/rooms/${roomId}/messages?${params}`);
      if (!res.ok) return [];
      return (await res.json()) as Message[];
    },
    [roomId],
  );

  // Load initial messages on room change
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setMessages([]);
    setHasMore(true);

    loadMessages().then((msgs) => {
      if (cancelled) return;
      setMessages(msgs.reverse());
      setHasMore(msgs.length >= 50);
      setLoading(false);
      requestAnimationFrame(() => {
        bottomRef.current?.scrollIntoView();
      });
    });

    return () => {
      cancelled = true;
    };
  }, [roomId, loadMessages]);

  // Scroll to bottom when new messages arrive if near bottom
  useEffect(() => {
    if (!loading && messages.length > 0) {
      const container = containerRef.current;
      if (!container) return;
      const isNearBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight <
        100;
      if (isNearBottom) {
        requestAnimationFrame(() =>
          bottomRef.current?.scrollIntoView({ behavior: "smooth" }),
        );
      }
    }
  }, [messages.length, loading]);

  const handleScroll = useCallback(async () => {
    const container = containerRef.current;
    if (!container || loadingMore || !hasMore) return;
    if (container.scrollTop < 200 && messages.length > 0) {
      setLoadingMore(true);
      const oldHeight = container.scrollHeight;
      const older = await loadMessages(messages[0].id);
      if (older.length === 0) {
        setHasMore(false);
      } else {
        setMessages((prev) => [...older.reverse(), ...prev]);
        setHasMore(older.length >= 50);
        requestAnimationFrame(() => {
          container.scrollTop = container.scrollHeight - oldHeight;
        });
      }
      setLoadingMore(false);
    }
  }, [loadingMore, hasMore, messages, loadMessages]);

  if (loading) {
    return <div className={styles.loading}>Loading messages...</div>;
  }

  return (
    <div className={styles.feed} ref={containerRef} onScroll={handleScroll}>
      {loadingMore && (
        <div className={styles.loadingMore}>Loading older messages...</div>
      )}
      {!hasMore && messages.length > 0 && (
        <div className={styles.beginning}>Beginning of conversation</div>
      )}
      {messages.length === 0 && (
        <div className={styles.empty}>
          No messages yet. Start the conversation!
        </div>
      )}
      {messages.map((msg, i) => {
        const prev = messages[i - 1];
        const showAuthor =
          !prev ||
          prev.author_id !== msg.author_id ||
          new Date(msg.created_at).getTime() -
            new Date(prev.created_at).getTime() >
            300_000;

        return (
          <div
            key={msg.id}
            className={`${styles.message} ${msg.deleted_at ? styles.deleted : ""}`}
          >
            {showAuthor && (
              <div className={styles.authorRow}>
                <span className={styles.avatar}>
                  {msg.author_avatar_url ? (
                    <img
                      src={msg.author_avatar_url}
                      alt=""
                      className={styles.avatarImg}
                    />
                  ) : (
                    (msg.author_display_name?.[0]?.toUpperCase() ?? "?")
                  )}
                </span>
                <span className={styles.authorName}>
                  {msg.author_display_name ?? "Deleted user"}
                </span>
                <span className={styles.timestamp}>
                  {timeAgo(msg.created_at)}
                </span>
              </div>
            )}
            {msg.deleted_at ? (
              <div className={styles.deletedText}>This message was deleted</div>
            ) : (
              <>
                <div
                  className={styles.body}
                  dangerouslySetInnerHTML={{ __html: msg.body_html }}
                />
                {msg.edited_at && (
                  <span className={styles.edited}>(edited)</span>
                )}
              </>
            )}
          </div>
        );
      })}
      {typingUsers.length > 0 && (
        <div className={styles.typing}>
          {typingUsers.join(", ")} {typingUsers.length === 1 ? "is" : "are"}{" "}
          typing...
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
