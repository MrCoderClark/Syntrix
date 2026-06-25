"use client";

import { useCallback, useEffect, useState } from "react";
import { RoomList } from "@/components/chat/RoomList";
import type { CommunityGroup, DM } from "@/components/chat/RoomList";
import styles from "./ChatView.module.css";

interface CommunityBrief {
  id: string;
  slug: string;
  name: string;
  color: string;
}

interface RoomBrief {
  id: string;
  community_id: string | null;
  name: string;
  slug: string;
  is_default: boolean;
  is_private: boolean;
  is_dm: boolean;
}

export function ChatView() {
  const [communities, setCommunities] = useState<CommunityGroup[]>([]);
  const [dms, setDms] = useState<DM[]>([]);
  const [activeRoomId, setActiveRoomId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [commRes, dmRes] = await Promise.all([
          fetch("/api/communities/mine"),
          fetch("/api/dms"),
        ]);

        const comms: CommunityBrief[] = commRes.ok ? await commRes.json() : [];
        const dmList: DM[] = dmRes.ok ? await dmRes.json() : [];

        const groups: CommunityGroup[] = [];
        for (const c of comms) {
          const roomRes = await fetch(`/api/communities/${c.id}/rooms`);
          const rooms: RoomBrief[] = roomRes.ok ? await roomRes.json() : [];
          groups.push({
            id: c.id,
            name: c.name,
            slug: c.slug,
            color: c.color,
            rooms,
          });
        }

        if (cancelled) return;
        setCommunities(groups);
        setDms(dmList);

        // Auto-select first default room
        if (!activeRoomId) {
          const firstDefault = groups
            .flatMap((g) => g.rooms)
            .find((r) => r.is_default);
          const firstRoom = firstDefault || groups[0]?.rooms[0];
          if (firstRoom) setActiveRoomId(firstRoom.id);
          else if (dmList[0]) setActiveRoomId(dmList[0].room_id);
        }
      } catch {
        // ignore fetch errors
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSelectRoom = useCallback((roomId: string) => {
    setActiveRoomId(roomId);
  }, []);

  if (loading) {
    return <div className={styles.loading}>Loading chat...</div>;
  }

  return (
    <div className={styles.chatView}>
      <div className={styles.roomListPanel}>
        <RoomList
          communities={communities}
          dms={dms}
          activeRoomId={activeRoomId}
          onSelectRoom={handleSelectRoom}
        />
      </div>
      <div className={styles.messagePanel}>
        {activeRoomId ? (
          <div className={styles.placeholder}>
            Select a room to start chatting
          </div>
        ) : (
          <div className={styles.placeholder}>No rooms available</div>
        )}
      </div>
    </div>
  );
}
