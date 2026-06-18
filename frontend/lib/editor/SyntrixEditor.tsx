"use client";

import { useRef } from "react";
import type { JSONContent } from "@tiptap/react";
import { EditorContent, useEditor } from "@tiptap/react";
import { getSyntrixExtensions } from "./extensions";
import styles from "./SyntrixEditor.module.css";

interface Props {
  initialContent?: JSONContent;
  placeholder?: string;
  onChange?: (json: JSONContent) => void;
}

export function SyntrixEditor({
  initialContent,
  placeholder,
  onChange,
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  const editor = useEditor({
    extensions: getSyntrixExtensions(placeholder),
    content: initialContent ?? { type: "doc", content: [] },
    onUpdate({ editor: e }) {
      onChange?.(e.getJSON());
    },
  });

  if (!editor) return null;

  async function handleImageUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !editor) return;

    try {
      const signRes = await fetch("/api/uploads/sign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          content_type: file.type,
        }),
      });
      if (!signRes.ok) throw new Error("Failed to sign");
      const { key, upload_url } = await signRes.json();

      const putRes = await fetch(upload_url, {
        method: "PUT",
        headers: { "Content-Type": file.type },
        body: file,
      });
      if (!putRes.ok) throw new Error("Upload failed");

      const finalRes = await fetch("/api/uploads/finalize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key }),
      });
      if (!finalRes.ok) throw new Error("Finalize failed");
      const { url } = await finalRes.json();

      editor.chain().focus().setImage({ src: url }).run();
    } catch {
      // silently fail — user can retry
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  }

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
          className={`${styles.tbtn} ${editor.isActive("heading", { level: 2 }) ? styles.active : ""}`}
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 2 }).run()
          }
          title="Heading"
        >
          H
        </button>
        <button
          type="button"
          className={`${styles.tbtn} ${editor.isActive("bulletList") ? styles.active : ""}`}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          title="Bullet list"
        >
          •
        </button>
        <button
          type="button"
          className={`${styles.tbtn} ${editor.isActive("orderedList") ? styles.active : ""}`}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          title="Numbered list"
        >
          1.
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
          className={`${styles.tbtn} ${editor.isActive("codeBlock") ? styles.active : ""}`}
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          title="Code block"
        >
          {"</>"}
        </button>
        <span className={styles.sep} />
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
        <button
          type="button"
          className={styles.tbtn}
          onClick={() => fileRef.current?.click()}
          title="Image"
        >
          📷
        </button>
        <button
          type="button"
          className={styles.tbtn}
          onClick={() => {
            const src = window.prompt("Video embed URL:");
            if (src) editor.chain().focus().setIframe({ src }).run();
          }}
          title="Embed video"
        >
          ▶
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          className={styles.hidden}
          onChange={handleImageUpload}
        />
      </div>
      <EditorContent editor={editor} className={styles.content} />
    </div>
  );
}
