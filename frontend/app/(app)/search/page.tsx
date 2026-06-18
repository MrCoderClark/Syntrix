"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Avatar } from "@/components/ui/Avatar";
import { timeAgo } from "@/lib/text";
import styles from "./page.module.css";

interface PostResult {
  id: string;
  title: string;
  community_slug: string | null;
  community_name: string | null;
  author_handle: string | null;
  score: number;
  comment_count: number;
  created_at: string;
}

interface CommunityResult {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  color: string;
  member_count: number;
}

interface UserResult {
  id: string;
  handle: string;
  display_name: string;
  avatar_url: string | null;
}

interface SearchData {
  posts: PostResult[];
  communities: CommunityResult[];
  users: UserResult[];
}

export default function SearchPage() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q") ?? "";
  const [data, setData] = useState<SearchData | null>(null);
  const [loading, setLoading] = useState(false);

  const doSearch = useCallback(async () => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q.trim())}`);
      if (res.ok) {
        setData(await res.json());
      }
    } catch {
      /* ignore */
    }
    setLoading(false);
  }, [q]);

  useEffect(() => {
    doSearch();
  }, [doSearch]);

  const hasResults =
    data &&
    (data.posts.length > 0 ||
      data.communities.length > 0 ||
      data.users.length > 0);

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>
        Search results for{" "}
        <span className={styles.query}>&ldquo;{q}&rdquo;</span>
      </h1>

      {loading ? (
        <p className={styles.status}>Searching...</p>
      ) : !q.trim() ? (
        <p className={styles.status}>Enter a search term above.</p>
      ) : !hasResults ? (
        <p className={styles.status}>No results found for &ldquo;{q}&rdquo;</p>
      ) : (
        <>
          {data!.communities.length > 0 && (
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Communities</h2>
              <div className={styles.list}>
                {data!.communities.map((c) => (
                  <Link
                    key={c.id}
                    href={`/c/${c.slug}`}
                    className={styles.card}
                  >
                    <span
                      className={styles.dot}
                      style={{ background: c.color }}
                    />
                    <div className={styles.cardBody}>
                      <span className={styles.cardTitle}>{c.name}</span>
                      <span className={styles.cardMeta}>
                        c/{c.slug} &middot; {c.member_count} members
                      </span>
                      {c.description && (
                        <span className={styles.cardDesc}>{c.description}</span>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {data!.users.length > 0 && (
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>People</h2>
              <div className={styles.list}>
                {data!.users.map((u) => {
                  const initials = (u.display_name ?? "?")
                    .split(" ")
                    .map((w) => w[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase();
                  return (
                    <Link
                      key={u.id}
                      href={`/u/${u.handle}`}
                      className={styles.card}
                    >
                      <Avatar
                        src={u.avatar_url ?? undefined}
                        alt={u.display_name}
                        fallback={initials}
                        size="sm"
                      />
                      <div className={styles.cardBody}>
                        <span className={styles.cardTitle}>
                          {u.display_name}
                        </span>
                        <span className={styles.cardMeta}>u/{u.handle}</span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </section>
          )}

          {data!.posts.length > 0 && (
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Posts</h2>
              <div className={styles.list}>
                {data!.posts.map((p) => (
                  <Link
                    key={p.id}
                    href={`/c/${p.community_slug}/post/${p.id}`}
                    className={styles.card}
                  >
                    <div className={styles.cardBody}>
                      <span className={styles.cardTitle}>{p.title}</span>
                      <span className={styles.cardMeta}>
                        {p.community_slug && `c/${p.community_slug}`}
                        {p.author_handle && ` · ${p.author_handle}`}
                        {` · ${p.score} pts · ${p.comment_count} comments · ${timeAgo(p.created_at)}`}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
