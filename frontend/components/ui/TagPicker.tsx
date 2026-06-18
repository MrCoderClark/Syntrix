"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { TagPill } from "./TagPill";
import styles from "./TagPicker.module.css";

interface TagOption {
  id: string;
  slug: string;
  name: string;
  color: string | null;
  usage_count: number;
}

interface TagPickerProps {
  communitySlug: string;
  selected: TagOption[];
  onChange: (tags: TagOption[]) => void;
  max?: number;
}

export function TagPicker({
  communitySlug,
  selected,
  onChange,
  max = 5,
}: TagPickerProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<TagOption[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const fetchTags = useCallback(
    async (q: string) => {
      const res = await fetch(
        `/api/communities/${communitySlug}/tags/autocomplete?q=${encodeURIComponent(q)}`,
      );
      if (!res.ok) return;
      const data: TagOption[] = await res.json();
      const selectedIds = new Set(selected.map((t) => t.id));
      setResults(data.filter((t) => !selectedIds.has(t.id)));
    },
    [communitySlug, selected],
  );

  useEffect(() => {
    if (!open) return;
    const timer = setTimeout(() => fetchTags(query), 150);
    return () => clearTimeout(timer);
  }, [query, open, fetchTags]);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  function addTag(tag: TagOption) {
    if (selected.length >= max) return;
    onChange([...selected, tag]);
    setQuery("");
  }

  function removeTag(id: string) {
    onChange(selected.filter((t) => t.id !== id));
  }

  return (
    <div className={styles.wrapper} ref={ref}>
      {selected.length > 0 && (
        <div className={styles.pills}>
          {selected.map((t) => (
            <TagPill
              key={t.id}
              name={t.name}
              color={t.color}
              onRemove={() => removeTag(t.id)}
            />
          ))}
        </div>
      )}
      {selected.length < max && (
        <input
          className={styles.input}
          placeholder="Search tags..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            setOpen(true);
            fetchTags(query);
          }}
        />
      )}
      {open && results.length > 0 && (
        <div className={styles.dropdown}>
          {results.map((t) => (
            <button
              key={t.id}
              type="button"
              className={styles.option}
              onClick={() => addTag(t)}
            >
              {t.color && (
                <span
                  className={styles.optionDot}
                  style={{ background: t.color }}
                />
              )}
              <span className={styles.optionName}>{t.name}</span>
              <span className={styles.optionCount}>
                {t.usage_count} question{t.usage_count !== 1 ? "s" : ""}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
