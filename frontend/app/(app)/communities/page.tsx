import Link from "next/link";
import { PageHeader, TitleAccent } from "@/components/ui/PageHeader";
import { CardArt } from "@/components/ui/CardArt";
import styles from "./page.module.css";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8001";

interface Community {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  color: string;
  member_count: number;
}

async function getCommunities(): Promise<Community[]> {
  const res = await fetch(`${BACKEND_URL}/api/communities`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return res.json();
}

export default async function CommunitiesPage() {
  const communities = await getCommunities();

  return (
    <>
      <PageHeader
        glyph="C"
        title={
          <>
            Browse <TitleAccent>communities</TitleAccent>
          </>
        }
        subtitle="Find your people — gamers, homelabbers, SREs, and devs."
      />

      {communities.length === 0 ? (
        <p className={styles.empty}>
          No communities yet. Check back soon or request one!
        </p>
      ) : (
        <div className={styles.grid}>
          {communities.map((c) => (
            <Link
              key={c.id}
              href={`/c/${c.slug}`}
              className={styles.card}
              style={{ "--community-color": c.color } as React.CSSProperties}
            >
              <div className={styles.art}>
                <CardArt color={c.color} id={`comm-${c.slug}`} />
              </div>
              <div className={styles.body}>
                <h3 className={styles.name}>{c.name}</h3>
                <span className={styles.slug}>c/{c.slug}</span>
                {c.description && (
                  <p className={styles.desc}>{c.description}</p>
                )}
                <span className={styles.members}>
                  {c.member_count} {c.member_count === 1 ? "member" : "members"}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
