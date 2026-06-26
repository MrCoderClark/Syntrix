"use client";

import type React from "react";
import { LockIcon, UsersIcon } from "@/components/icons";
import styles from "./RoomHeader.module.css";

interface RoomHeaderProps {
  roomName: string;
  isPrivate: boolean;
  isDm: boolean;
  memberCount: number;
  description?: string;
  dmInitial?: string;
  mobileToggle?: React.ReactNode;
}

export function RoomHeader({
  roomName,
  isPrivate,
  isDm,
  memberCount,
  description,
  dmInitial,
  mobileToggle,
}: RoomHeaderProps) {
  return (
    <div className={styles.header}>
      <div className={styles.info}>
        {mobileToggle}
        {isDm ? (
          <>
            <span className={styles.dmAvatar}>
              {dmInitial ?? roomName[0]?.toUpperCase() ?? "?"}
            </span>
            <div className={styles.dmMeta}>
              <span className={styles.name}>{roomName}</span>
            </div>
          </>
        ) : (
          <>
            <span className={styles.hash}>
              {isPrivate ? <LockIcon size={15} /> : "#"}
            </span>
            <span className={styles.name}>{roomName}</span>
            {description && (
              <>
                <span className={styles.divider} />
                <span className={styles.description}>{description}</span>
              </>
            )}
          </>
        )}
      </div>
      {!isDm && (
        <div className={styles.actions}>
          <span className={styles.members}>
            <UsersIcon size={14} />
            {memberCount}
          </span>
        </div>
      )}
    </div>
  );
}
