import { PageHeader, TitleAccent } from "@/components/ui/PageHeader";
import { TabStrip, Tab } from "@/components/ui/Tab";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { FilterIcon } from "@/components/icons";
import styles from "./page.module.css";

const POSTS = [
  {
    communitySlug: "homelab",
    communityColor: "var(--c-homelab)",
    title: "Anyone running Proxmox + Ceph on consumer NVMe?",
    author: { name: "u/glados", avatarFallback: "G" },
    date: "4h",
    score: 247,
    commentCount: 38,
    pinned: true,
  },
  {
    communitySlug: "halo",
    communityColor: "var(--c-halo)",
    title: "Ranked sensitivity setup: my unhinged calibration guide",
    author: {
      name: "u/recoil",
      avatarFallback: "R",
      avatarBg: "#e9b1a4",
      avatarColor: "#5d2424",
    },
    date: "6h",
    score: 184,
    commentCount: 12,
  },
  {
    communitySlug: "sre",
    communityColor: "var(--c-sre)",
    title: "RFC: monorepo layout for a small platform team",
    author: {
      name: "u/devops_dan",
      avatarFallback: "D",
      avatarBg: "#d4b8e8",
      avatarColor: "#3a2347",
    },
    date: "9h",
    score: 91,
    commentCount: 24,
  },
  {
    communitySlug: "proxmox",
    communityColor: "var(--c-proxmox)",
    title: "My homelab finally stopped tripping the breaker — full build log",
    author: {
      name: "u/rackmount",
      avatarFallback: "R",
      avatarBg: "#c4d28a",
      avatarColor: "#354823",
    },
    date: "1d",
    score: 412,
    commentCount: 87,
  },
  {
    communitySlug: "golang",
    communityColor: "var(--c-golang)",
    title: "A pragmatic guide to errors.Join in real codebases",
    author: {
      name: "u/mike_g",
      avatarFallback: "M",
      avatarBg: "#a8e5e5",
      avatarColor: "#0d4d57",
    },
    date: "1d",
    score: 156,
    commentCount: 31,
  },
  {
    communitySlug: "security",
    communityColor: "var(--c-sec)",
    title: "Patched a 0-day in our own internal portal — postmortem inside",
    author: {
      name: "u/anon_blue",
      avatarFallback: "A",
      avatarBg: "#e3a89c",
      avatarColor: "#4a1e1e",
    },
    date: "2d",
    score: 628,
    commentCount: 154,
  },
];

const STAGGER_DELAYS = ["50ms", "120ms", "190ms", "260ms", "330ms", "400ms"];

export default function HomePage() {
  return (
    <>
      <PageHeader
        glyph="S"
        eyebrow="Phase 1 &middot; Communities & Posts"
        title={
          <>
            Your <TitleAccent>feed</TitleAccent>
          </>
        }
        subtitle="Hot across the communities you follow — gamers, IT admins, and devs, in the order the room finds interesting."
        actions={
          <>
            <Button>Customize</Button>
            <Button>
              <FilterIcon />
              Filter
            </Button>
          </>
        }
      />

      <TabStrip className={styles.tabs}>
        <Tab active count="247">
          Hot
        </Tab>
        <Tab>New</Tab>
        <Tab>Top this week</Tab>
        <Tab>Discussions</Tab>
        <Tab>Following</Tab>
      </TabStrip>

      <div className={styles.grid}>
        {POSTS.map((post, i) => (
          <Card
            key={post.communitySlug}
            {...post}
            animationDelay={STAGGER_DELAYS[i]}
          />
        ))}
      </div>
    </>
  );
}
