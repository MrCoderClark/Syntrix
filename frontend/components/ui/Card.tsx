import { CardArt } from "./CardArt";
import { VoteWidget } from "./VoteWidget";
import { Avatar } from "./Avatar";
import { CommentIcon, BookmarkIcon } from "@/components/icons";
import styles from "./Card.module.css";

interface CardProps {
  communitySlug: string;
  communityColor: string;
  title: string;
  author: {
    name: string;
    avatarFallback: string;
    avatarBg?: string;
    avatarColor?: string;
  };
  date: string;
  score: number;
  commentCount: number;
  pinned?: boolean;
  animationDelay?: string;
}

export function Card({
  communitySlug,
  communityColor,
  title,
  author,
  date,
  score,
  commentCount,
  pinned,
  animationDelay,
}: CardProps) {
  return (
    <article
      className={styles.card}
      style={animationDelay ? { animationDelay } : undefined}
    >
      <div className={styles.art} style={{ background: communityColor }}>
        <CardArt color={communityColor} id={`card-${communitySlug}`} />
        <span className={styles.corner}>c/{communitySlug}</span>
        {pinned && <span className={styles.pin}>&#9733; pinned</span>}
      </div>
      <div className={styles.body}>
        <h3 className={styles.title}>{title}</h3>
        <div className={styles.author}>
          <Avatar
            alt={author.name}
            fallback={author.avatarFallback}
            size="sm"
            bgColor={author.avatarBg}
            fgColor={author.avatarColor}
          />
          <span className={styles.authorName}>{author.name}</span>
          <span className={styles.authorDate}>&middot; {date}</span>
        </div>
      </div>
      <div className={styles.meta}>
        <VoteWidget score={score} />
        <button className={styles.metaChip}>
          <CommentIcon />
          <span className={styles.chipCount}>{commentCount}</span>
        </button>
        <button className={styles.metaChip}>
          <BookmarkIcon />
        </button>
      </div>
    </article>
  );
}
