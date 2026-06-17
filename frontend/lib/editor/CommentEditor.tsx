"use client";

import type { JSONContent } from "@tiptap/react";
import { EditorContent, useEditor } from "@tiptap/react";
import TiptapLink from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";
import styles from "./CommentEditor.module.css";

interface Props {
  placeholder?: string;
  onChange?: (json: JSONContent) => void;
  onSubmit?: () => void;
  editorRef?: React.MutableRefObject<ReturnType<typeof useEditor> | null>;
}

function getCommentExtensions(placeholder?: string) {
  return [
    StarterKit.configure({
      codeBlock: false,
      heading: false,
      horizontalRule: false,
    }),
    TiptapLink.configure({ openOnClick: false, autolink: true }),
    Placeholder.configure({
      placeholder: placeholder ?? "Write a comment...",
    }),
  ];
}

export function CommentEditor({
  placeholder,
  onChange,
  onSubmit,
  editorRef,
}: Props) {
  const editor = useEditor({
    extensions: getCommentExtensions(placeholder),
    content: { type: "doc", content: [] },
    onUpdate({ editor: e }) {
      onChange?.(e.getJSON());
    },
  });

  if (editorRef) editorRef.current = editor;

  if (!editor) return null;

  return (
    <div className={styles.wrapper}>
      <div className={styles.toolbar}>
        <button
          type="button"
          className={`${styles.tbtn} ${editor.isActive("bold") ? styles.active : ""}`}
          onClick={() => editor.chain().focus().toggleBold().run()}
          title="Bold"
        >
          B
        </button>
        <button
          type="button"
          className={`${styles.tbtn} ${editor.isActive("italic") ? styles.active : ""}`}
          onClick={() => editor.chain().focus().toggleItalic().run()}
          title="Italic"
        >
          <em>I</em>
        </button>
        <button
          type="button"
          className={`${styles.tbtn} ${editor.isActive("strike") ? styles.active : ""}`}
          onClick={() => editor.chain().focus().toggleStrike().run()}
          title="Strikethrough"
        >
          <s>S</s>
        </button>
        <span className={styles.sep} />
        <button
          type="button"
          className={`${styles.tbtn} ${editor.isActive("code") ? styles.active : ""}`}
          onClick={() => editor.chain().focus().toggleCode().run()}
          title="Inline code"
        >
          {"<>"}
        </button>
        <button
          type="button"
          className={`${styles.tbtn} ${editor.isActive("blockquote") ? styles.active : ""}`}
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          title="Quote"
        >
          &ldquo;
        </button>
        <button
          type="button"
          className={styles.tbtn}
          onClick={() => {
            const url = window.prompt("Link URL:");
            if (url) editor.chain().focus().setLink({ href: url }).run();
          }}
          title="Link"
        >
          🔗
        </button>
        {onSubmit && (
          <>
            <span className={styles.sep} />
            <button
              type="button"
              className={styles.submitBtn}
              onClick={onSubmit}
            >
              Reply
            </button>
          </>
        )}
      </div>
      <EditorContent editor={editor} className={styles.content} />
    </div>
  );
}
