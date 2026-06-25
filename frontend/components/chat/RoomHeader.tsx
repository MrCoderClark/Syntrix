"use client";

import { UsersIcon } from "@/components/icons";
import styles from "./RoomHeader.module.css";

interface RoomHeaderProps {
  roomName: string;
  isPrivate: boolean;
  isDm: boolean;
  memberCount: number;
}

export function RoomHeader({
  roomName,
  isPrivate,
  isDm,
  memberCount,
}: RoomHeaderProps) {
  return (
    <div className={styles.header}>
      <div className={styles.info}>
        {!isDm && <span className={styles.hash}>{isPrivate ? "🔒" : "#"}</span>}
        <span className={styles.name}>{roomName}</span>
      </div>
      <div className={styles.actions}>
        <span className={styles.members}>
          <UsersIcon size={14} />
          {memberCount}
        </span>
      </div>
    </div>
  );
}
