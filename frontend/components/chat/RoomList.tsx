"use client";

import styles from "./RoomList.module.css";

interface Room {
  id: string;
  community_id: string | null;
  name: string;
  slug: string;
  is_default: boolean;
  is_private: boolean;
  is_dm: boolean;
}

interface DM {
  room_id: string;
  other_user_id: string;
  other_user_handle: string;
  other_user_display_name: string;
  other_user_avatar_url: string | null;
  last_message_body_html: string | null;
  last_message_at: string | null;
}

interface CommunityGroup {
  id: string;
  name: string;
  slug: string;
  color: string;
  rooms: Room[];
}

interface RoomListProps {
  communities: CommunityGroup[];
  dms: DM[];
  activeRoomId: string | null;
  onSelectRoom: (roomId: string) => void;
}

export type { Room, DM, CommunityGroup };

export function RoomList({
  communities,
  dms,
  activeRoomId,
  onSelectRoom,
}: RoomListProps) {
  return (
    <div className={styles.list}>
      {dms.length > 0 && (
        <>
          <div className={styles.sectionLabel}>Direct Messages</div>
          {dms.map((dm) => (
            <button
              key={dm.room_id}
              className={`${styles.roomItem} ${dm.room_id === activeRoomId ? styles.active : ""}`}
              onClick={() => onSelectRoom(dm.room_id)}
            >
              <span className={styles.dmAvatar}>
                {dm.other_user_display_name[0]?.toUpperCase()}
              </span>
              <div className={styles.roomInfo}>
                <span className={styles.roomName}>
                  {dm.other_user_display_name}
                </span>
                {dm.last_message_body_html && (
                  <span
                    className={styles.lastMsg}
                    dangerouslySetInnerHTML={{
                      __html: dm.last_message_body_html
                        .replace(/<[^>]+>/g, "")
                        .slice(0, 40),
                    }}
                  />
                )}
              </div>
            </button>
          ))}
        </>
      )}

      {communities.map((c) => (
        <div key={c.id}>
          <div className={styles.sectionLabel}>
            <span
              className={styles.communityDot}
              style={{ background: c.color }}
            />
            {c.name}
          </div>
          {c.rooms.map((room) => (
            <button
              key={room.id}
              className={`${styles.roomItem} ${room.id === activeRoomId ? styles.active : ""}`}
              onClick={() => onSelectRoom(room.id)}
            >
              <span className={styles.hash}>
                {room.is_private ? "🔒" : "#"}
              </span>
              <span className={styles.roomName}>{room.name}</span>
            </button>
          ))}
        </div>
      ))}

      {communities.length === 0 && dms.length === 0 && (
        <div className={styles.empty}>Join a community to start chatting</div>
      )}
    </div>
  );
}
