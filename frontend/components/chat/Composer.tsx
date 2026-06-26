"use client";

import { useCallback, useRef } from "react";
import type { JSONContent } from "@tiptap/react";
import { EditorContent, useEditor } from "@tiptap/react";
import TiptapLink from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";
import { LinkIcon } from "@/components/icons";
import styles from "./Composer.module.css";

interface ComposerProps {
  roomId: string;
  onMessageSent?: () => void;
  onTyping?: () => void;
}

const EXTENSIONS = [
  StarterKit.configure({
    codeBlock: false,
    heading: false,
    horizontalRule: false,
  }),
  TiptapLink.configure({ openOnClick: false, autolink: true }),
  Placeholder.configure({ placeholder: "Type a message..." }),
];

function isEmptyDoc(json: JSONContent): boolean {
  if (!json.content || json.content.length === 0) return true;
  return json.content.every(
    (node) =>
      node.type === "paragraph" && (!node.content || node.content.length === 0),
  );
}

export function Composer({ roomId, onMessageSent, onTyping }: ComposerProps) {
  const sendingRef = useRef(false);
  const handleSendRef = useRef<() => void>(() => {});
  const lastTypingRef = useRef(0);

  const editor = useEditor({
    extensions: EXTENSIONS,
    content: { type: "doc", content: [] },
    onUpdate() {
      const now = Date.now();
      if (now - lastTypingRef.current > 2000) {
        lastTypingRef.current = now;
        onTyping?.();
      }
    },
    editorProps: {
      handleKeyDown(_view, event) {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          handleSendRef.current();
          return true;
        }
        return false;
      },
    },
  });

  const handleSend = useCallback(async () => {
    if (!editor || sendingRef.current) return;
    const json = editor.getJSON();
    if (isEmptyDoc(json)) return;

    sendingRef.current = true;
    try {
      const res = await fetch(`/api/rooms/${roomId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body_json: json }),
      });
      if (res.ok) {
        editor.commands.clearContent();
        onMessageSent?.();
      }
    } finally {
      sendingRef.current = false;
    }
  }, [editor, roomId, onMessageSent]);

  handleSendRef.current = handleSend;

  if (!editor) return null;

  return (
    <div className={styles.composer}>
      <div className={styles.card}>
        <div className={styles.toolbar}>
          <button
            type="button"
            className={`${styles.toolbarBtn} ${editor.isActive("bold") ? styles.toolbarActive : ""}`}
            onClick={() => editor.chain().focus().toggleBold().run()}
            title="Bold (Ctrl+B)"
            aria-label="Bold"
          >
            B
          </button>
          <button
            type="button"
            className={`${styles.toolbarBtn} ${editor.isActive("italic") ? styles.toolbarActive : ""}`}
            onClick={() => editor.chain().focus().toggleItalic().run()}
            title="Italic (Ctrl+I)"
            aria-label="Italic"
            style={{ fontStyle: "italic" }}
          >
            I
          </button>
          <button
            type="button"
            className={`${styles.toolbarBtn} ${editor.isActive("code") ? styles.toolbarActive : ""}`}
            onClick={() => editor.chain().focus().toggleCode().run()}
            title="Inline code"
            aria-label="Code"
            style={{ fontFamily: "var(--font-mono-family)", fontSize: "12px" }}
          >
            {"<>"}
          </button>
          <div className={styles.toolbarDivider} />
          <button
            type="button"
            className={`${styles.toolbarBtn} ${editor.isActive("link") ? styles.toolbarActive : ""}`}
            onClick={() => {
              if (editor.isActive("link")) {
                editor.chain().focus().unsetLink().run();
              } else {
                const url = window.prompt("URL:");
                if (url) editor.chain().focus().setLink({ href: url }).run();
              }
            }}
            title="Link"
            aria-label="Link"
          >
            <LinkIcon size={14} />
          </button>
        </div>
        <div className={styles.editorWrap}>
          <EditorContent editor={editor} className={styles.content} />
        </div>
        <div className={styles.footer}>
          <div className={styles.hints}>
            <span>
              <span className={styles.kbd}>Enter</span> send
            </span>
            <span>
              <span className={styles.kbd}>Shift+Enter</span> newline
            </span>
          </div>
          <button
            type="button"
            className={styles.sendBtn}
            onClick={handleSend}
            aria-label="Send message"
            title="Send (Enter)"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              width="16"
              height="16"
              aria-hidden="true"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
