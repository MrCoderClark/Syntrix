"use client";

import { useCallback, useRef } from "react";
import type { JSONContent } from "@tiptap/react";
import { EditorContent, useEditor } from "@tiptap/react";
import TiptapLink from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";
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

  const editor = useEditor({
    extensions: EXTENSIONS,
    content: { type: "doc", content: [] },
    onUpdate() {
      onTyping?.();
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
      <div className={styles.editorWrap}>
        <EditorContent editor={editor} className={styles.content} />
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
          width="18"
          height="18"
          aria-hidden="true"
        >
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </div>
  );
}
