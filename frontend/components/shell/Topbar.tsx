import { SearchIcon, PlusIcon, MessageIcon } from "@/components/icons";
import { Button } from "@/components/ui/Button";
import { IconButton } from "@/components/ui/IconButton";
import { Avatar } from "@/components/ui/Avatar";
import styles from "./Topbar.module.css";

export function Topbar() {
  return (
    <div className={styles.topbar}>
      <div className={styles.search}>
        <SearchIcon size={16} style={{ color: "var(--ink-faint)" }} />
        <input
          type="text"
          className={styles.searchInput}
          placeholder="Search communities, posts, people..."
        />
        <span className={styles.kbd}>&#8984; K</span>
      </div>
      <Button variant="primary">
        <PlusIcon />
        New post
      </Button>
      <IconButton aria-label="messages">
        <MessageIcon />
      </IconButton>
      <Avatar alt="profile" fallback="KC" />
    </div>
  );
}
