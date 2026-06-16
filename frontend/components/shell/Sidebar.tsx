import { Wordmark } from "@/components/Wordmark";
import { HomeIcon, SearchIcon, BellIcon, UserIcon } from "@/components/icons";
import styles from "./Sidebar.module.css";

interface NavItem {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  badge?: string;
}

interface CommunityItem {
  slug: string;
  color: string;
  members: string;
}

const NAV_ITEMS: NavItem[] = [
  { icon: <HomeIcon />, label: "Feed", active: true },
  { icon: <SearchIcon />, label: "Explore" },
  { icon: <BellIcon />, label: "Notifications", badge: "12" },
  { icon: <UserIcon />, label: "My profile" },
];

const COMMUNITIES: CommunityItem[] = [
  { slug: "homelab", color: "var(--c-homelab)", members: "48.2k" },
  { slug: "halo", color: "var(--c-halo)", members: "31.6k" },
  { slug: "sre", color: "var(--c-sre)", members: "22.8k" },
  { slug: "proxmox", color: "var(--c-proxmox)", members: "14.0k" },
  { slug: "golang", color: "var(--c-golang)", members: "39.1k" },
  { slug: "security", color: "var(--c-sec)", members: "28.5k" },
];

export function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.wordmarkWrap}>
        <Wordmark />
      </div>

      <div className={styles.navLabel}>For you</div>
      <ul>
        {NAV_ITEMS.map((item) => (
          <li key={item.label}>
            <button
              className={`${styles.navItem}${item.active ? ` ${styles.active}` : ""}`}
            >
              <span className={styles.icon}>{item.icon}</span>
              <span>{item.label}</span>
              {item.badge && <span className={styles.badge}>{item.badge}</span>}
            </button>
          </li>
        ))}
      </ul>

      <div className={styles.navLabel}>Communities</div>
      <ul>
        {COMMUNITIES.map((c) => (
          <li key={c.slug}>
            <button className={styles.communityItem}>
              <span
                className={styles.communityDot}
                style={{ background: c.color }}
              />
              <span>c/{c.slug}</span>
              <span className={styles.members}>{c.members}</span>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
