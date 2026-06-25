"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { timeAgo } from "@/lib/text";
import { MessageActions } from "./MessageActions";
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
  messages: Message[];
  loading: boolean;
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
  typingUsers?: string[];
  currentUserId: string | null;
  onEditMessage?: (messageId: string, bodyJson: object) => void;
  onDeleteMessage?: (messageId: string) => void;
}

function EditInput({
  initialText,
  onSave,
  onCancel,
}: {
  initialText: string;
  onSave: (text: string) => void;
  onCancel: () => void;
}) {
  const [text, setText] = useState(initialText);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div className={styles.editWrap}>
      <input
        ref={inputRef}
        className={styles.editInput}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && text.trim()) onSave(text.trim());
          if (e.key === "Escape") onCancel();
        }}
      />
      <span className={styles.editHint}>Enter to save · Escape to cancel</span>
    </div>
  );
}

export function MessageFeed({
  roomId: _roomId,
  messages,
  loading,
  hasMore,
  loadingMore,
  onLoadMore,
  typingUsers = [],
  currentUserId,
  onEditMessage,
  onDeleteMessage,
}: MessageFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [editingId, setEditingId] = useState<string | null>(null);

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

  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container || loadingMore || !hasMore) return;
    if (container.scrollTop < 200 && messages.length > 0) {
      onLoadMore();
    }
  }, [loadingMore, hasMore, messages.length, onLoadMore]);

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

        const isOwn = currentUserId !== null && currentUserId === msg.author_id;
        const canSeeActions = !msg.deleted_at && currentUserId !== null;

        return (
          <div
            key={msg.id}
            className={`${styles.message} ${msg.deleted_at ? styles.deleted : ""}`}
          >
            {canSeeActions && (
              <div className={styles.actionsSlot}>
                <MessageActions
                  isOwn={isOwn}
                  onEdit={isOwn ? () => setEditingId(msg.id) : undefined}
                  onDelete={() => onDeleteMessage?.(msg.id)}
                />
              </div>
            )}
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
            ) : editingId === msg.id ? (
              <EditInput
                initialText={msg.body_html.replace(/<[^>]+>/g, "")}
                onSave={(text) => {
                  onEditMessage?.(msg.id, {
                    type: "doc",
                    content: [
                      {
                        type: "paragraph",
                        content: [{ type: "text", text }],
                      },
                    ],
                  });
                  setEditingId(null);
                }}
                onCancel={() => setEditingId(null)}
              />
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
