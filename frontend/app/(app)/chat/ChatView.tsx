"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useWebSocket } from "@/lib/ws";
import { RoomList } from "@/components/chat/RoomList";
import { CreateRoomModal } from "@/components/chat/CreateRoomModal";
import { NewDmModal } from "@/components/chat/NewDmModal";
import { MessageFeed } from "@/components/chat/MessageFeed";
import { Composer } from "@/components/chat/Composer";
import { RoomHeader } from "@/components/chat/RoomHeader";
import { MenuIcon, XIcon } from "@/components/icons";
import type { CommunityGroup, DM } from "@/components/chat/RoomList";
import type { Message } from "@/components/chat/MessageFeed";
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
  const [sidebarLoading, setSidebarLoading] = useState(true);
  const [createRoomFor, setCreateRoomFor] = useState<{
    communityId: string;
    communityName: string;
  } | null>(null);
  const [mobileRoomListOpen, setMobileRoomListOpen] = useState(false);
  const [showNewDm, setShowNewDm] = useState(false);

  // Current user
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setCurrentUserId(data.id);
      })
      .catch(() => {});
  }, []);

  // Derive active room metadata
  const activeRoom = useMemo(() => {
    if (!activeRoomId) return null;
    for (const c of communities) {
      const room = c.rooms.find((r) => r.id === activeRoomId);
      if (room)
        return { name: room.name, isPrivate: room.is_private, isDm: false };
    }
    const dm = dms.find((d) => d.room_id === activeRoomId);
    if (dm)
      return { name: dm.other_user_display_name, isPrivate: false, isDm: true };
    return null;
  }, [activeRoomId, communities, dms]);

  // Member count for active room
  const [memberCount, setMemberCount] = useState(0);

  useEffect(() => {
    if (!activeRoomId) return;
    fetch(`/api/rooms/${activeRoomId}/members`)
      .then((r) => (r.ok ? r.json() : []))
      .then((members: unknown[]) => setMemberCount(members.length))
      .catch(() => {});
  }, [activeRoomId]);

  // Message state (owned here, passed down to MessageFeed)
  const [messages, setMessages] = useState<Message[]>([]);
  const [msgLoading, setMsgLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  // Typing indicators
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const typingTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(
    new Map(),
  );

  // WebSocket
  const { status: wsStatus, send, lastMessage } = useWebSocket();
  const statusClass =
    wsStatus === "connected"
      ? styles.statusConnected
      : wsStatus === "connecting"
        ? styles.statusConnecting
        : styles.statusDisconnected;
  const prevRoomRef = useRef<string | null>(null);
  const activeRoomRef = useRef<string | null>(null);
  activeRoomRef.current = activeRoomId;

  // Load sidebar data once on mount
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

        const groups: CommunityGroup[] = await Promise.all(
          comms.map(async (c) => {
            const roomRes = await fetch(`/api/communities/${c.id}/rooms`);
            const rooms: RoomBrief[] = roomRes.ok ? await roomRes.json() : [];
            return {
              id: c.id,
              name: c.name,
              slug: c.slug,
              color: c.color,
              rooms,
            };
          }),
        );

        if (cancelled) return;
        setCommunities(groups);
        setDms(dmList);

        // Auto-select first default room
        const firstDefault = groups
          .flatMap((g) => g.rooms)
          .find((r) => r.is_default);
        const firstRoom = firstDefault || groups[0]?.rooms[0];
        if (firstRoom) setActiveRoomId(firstRoom.id);
        else if (dmList[0]) setActiveRoomId(dmList[0].room_id);
      } catch {
        // ignore fetch errors
      } finally {
        if (!cancelled) setSidebarLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  // Load messages when active room changes
  useEffect(() => {
    if (!activeRoomId) return;
    let cancelled = false;

    setMsgLoading(true);
    setMessages([]);
    setHasMore(true);
    setLoadingMore(false);
    setTypingUsers([]);
    for (const timer of typingTimers.current.values()) clearTimeout(timer);
    typingTimers.current.clear();

    fetch(`/api/rooms/${activeRoomId}/messages?limit=50`)
      .then((r) => (r.ok ? r.json() : []))
      .then((msgs: Message[]) => {
        if (cancelled) return;
        setMessages(msgs.reverse());
        setHasMore(msgs.length >= 50);
        setMsgLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeRoomId]);

  // WS room subscribe / unsubscribe when room changes or connection is established
  useEffect(() => {
    if (wsStatus !== "connected") return;
    // Unsubscribe from previous room if it changed
    if (prevRoomRef.current && prevRoomRef.current !== activeRoomId) {
      send({
        type: "room.unsubscribe",
        payload: { room_id: prevRoomRef.current },
      });
    }
    if (activeRoomId) {
      send({ type: "room.subscribe", payload: { room_id: activeRoomId } });
    }
    prevRoomRef.current = activeRoomId;
  }, [activeRoomId, wsStatus, send]);

  // Dispatch incoming WS messages
  useEffect(() => {
    if (!lastMessage) return;
    const { type, payload } = lastMessage;

    if (type === "message.created") {
      const msg = payload as unknown as Message;
      if (msg.room_id === activeRoomId) {
        setMessages((prev) => {
          if (prev.some((m) => m.id === msg.id)) return prev;
          return [...prev, msg];
        });
      }
    } else if (type === "message.edited") {
      const msg = payload as unknown as Message;
      setMessages((prev) => prev.map((m) => (m.id === msg.id ? msg : m)));
    } else if (type === "message.deleted") {
      const { id } = payload as { id: string };
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id
            ? {
                ...m,
                deleted_at: new Date().toISOString(),
                body_html: "",
                body_json: null,
              }
            : m,
        ),
      );
    } else if (type === "typing.start") {
      const userId = payload.user_id as string;
      setTypingUsers((prev) =>
        prev.includes(userId) ? prev : [...prev, userId],
      );
      const existing = typingTimers.current.get(userId);
      if (existing) clearTimeout(existing);
      typingTimers.current.set(
        userId,
        setTimeout(() => {
          setTypingUsers((prev) => prev.filter((u) => u !== userId));
          typingTimers.current.delete(userId);
        }, 3000),
      );
    } else if (type === "typing.stop") {
      const userId = payload.user_id as string;
      setTypingUsers((prev) => prev.filter((u) => u !== userId));
      const existing = typingTimers.current.get(userId);
      if (existing) {
        clearTimeout(existing);
        typingTimers.current.delete(userId);
      }
    }
  }, [lastMessage, activeRoomId]);

  // Load older messages (pagination)
  const handleLoadMore = useCallback(async () => {
    if (!activeRoomId || loadingMore || !hasMore || messages.length === 0)
      return;
    const roomAtCallTime = activeRoomId;
    setLoadingMore(true);
    const params = new URLSearchParams({ before: messages[0].id, limit: "50" });
    const res = await fetch(`/api/rooms/${roomAtCallTime}/messages?${params}`);
    if (roomAtCallTime !== activeRoomRef.current) return;
    const older: Message[] = res.ok ? await res.json() : [];
    if (older.length === 0) {
      setHasMore(false);
    } else {
      setMessages((prev) => [...older.reverse(), ...prev]);
      setHasMore(older.length >= 50);
    }
    setLoadingMore(false);
  }, [activeRoomId, loadingMore, hasMore, messages]);

  const handleSelectRoom = useCallback((roomId: string) => {
    setActiveRoomId(roomId);
    setMobileRoomListOpen(false);
  }, []);

  const handleCreateRoom = useCallback(
    (communityId: string) => {
      const community = communities.find((c) => c.id === communityId);
      if (community)
        setCreateRoomFor({ communityId, communityName: community.name });
    },
    [communities],
  );

  const handleRoomCreated = useCallback(
    (room: {
      id: string;
      name: string;
      slug: string;
      is_private: boolean;
      is_default: boolean;
      is_dm: boolean;
      community_id: string | null;
    }) => {
      setCommunities((prev) =>
        prev.map((c) =>
          c.id === room.community_id ? { ...c, rooms: [...c.rooms, room] } : c,
        ),
      );
      setActiveRoomId(room.id);
      setCreateRoomFor(null);
    },
    [],
  );

  const handleNewDm = useCallback(() => setShowNewDm(true), []);

  const handleDmCreated = useCallback((roomId: string) => {
    setShowNewDm(false);
    setActiveRoomId(roomId);
    fetch("/api/dms")
      .then((r) => (r.ok ? r.json() : []))
      .then(setDms);
  }, []);

  const handleEditMessage = useCallback(
    async (messageId: string, bodyJson: object) => {
      const res = await fetch(`/api/messages/${messageId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body_json: bodyJson }),
      });
      if (!res.ok) {
        alert("Failed to edit message");
        return;
      }
      const updated = await res.json();
      setMessages((prev) =>
        prev.map((m) => (m.id === updated.id ? updated : m)),
      );
    },
    [],
  );

  const handleDeleteMessage = useCallback(async (messageId: string) => {
    if (!confirm("Delete this message?")) return;
    const res = await fetch(`/api/messages/${messageId}`, { method: "DELETE" });
    if (!res.ok) {
      alert("Failed to delete message");
      return;
    }
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId
          ? {
              ...m,
              deleted_at: new Date().toISOString(),
              body_html: "",
              body_json: null,
            }
          : m,
      ),
    );
  }, []);

  const handleTyping = useCallback(() => {
    if (activeRoomId) {
      send({ type: "typing.start", payload: { room_id: activeRoomId } });
    }
  }, [activeRoomId, send]);

  if (sidebarLoading) {
    return <div className={styles.loading}>Loading chat...</div>;
  }

  return (
    <>
      <div className={styles.chatView}>
        <div
          className={`${styles.roomListPanel} ${mobileRoomListOpen ? styles.roomListOpen : ""}`}
        >
          <RoomList
            communities={communities}
            dms={dms}
            activeRoomId={activeRoomId}
            onSelectRoom={handleSelectRoom}
            onCreateRoom={handleCreateRoom}
            onNewDm={handleNewDm}
          />
        </div>
        {mobileRoomListOpen && (
          <div
            className={styles.mobileOverlay}
            onClick={() => setMobileRoomListOpen(false)}
          />
        )}
        <div className={styles.messagePanel}>
          {activeRoomId ? (
            <>
              <div className={`${styles.statusBar} ${statusClass}`}>
                <span className={styles.statusDot} aria-hidden="true" />
                {wsStatus === "connected"
                  ? "Connected"
                  : wsStatus === "connecting"
                    ? "Connecting..."
                    : "Disconnected"}
              </div>
              {activeRoom && (
                <RoomHeader
                  roomName={activeRoom.name}
                  isPrivate={activeRoom.isPrivate}
                  isDm={activeRoom.isDm}
                  memberCount={memberCount}
                  dmInitial={
                    activeRoom.isDm
                      ? activeRoom.name[0]?.toUpperCase()
                      : undefined
                  }
                  mobileToggle={
                    <button
                      className={styles.mobileMenuBtn}
                      onClick={() => setMobileRoomListOpen((o) => !o)}
                      aria-label="Toggle room list"
                      aria-expanded={mobileRoomListOpen}
                    >
                      {mobileRoomListOpen ? <XIcon /> : <MenuIcon />}
                    </button>
                  }
                />
              )}
              <MessageFeed
                key={activeRoomId}
                roomId={activeRoomId}
                roomName={activeRoom?.name}
                isDm={activeRoom?.isDm}
                messages={messages}
                loading={msgLoading}
                hasMore={hasMore}
                loadingMore={loadingMore}
                onLoadMore={handleLoadMore}
                typingUsers={typingUsers}
                currentUserId={currentUserId}
                onEditMessage={handleEditMessage}
                onDeleteMessage={handleDeleteMessage}
              />
              <Composer
                roomId={activeRoomId}
                placeholder={
                  activeRoom?.isDm
                    ? `Message ${activeRoom.name}`
                    : "Type a message..."
                }
                onMessageSent={(created) => {
                  const msg = created as unknown as Message;
                  if (msg.room_id === activeRoomRef.current) {
                    setMessages((prev) =>
                      prev.some((m) => m.id === msg.id) ? prev : [...prev, msg],
                    );
                  }
                }}
                onTyping={handleTyping}
              />
            </>
          ) : (
            <div className={styles.placeholder}>No rooms available</div>
          )}
        </div>
      </div>
      {createRoomFor && (
        <CreateRoomModal
          communityId={createRoomFor.communityId}
          communityName={createRoomFor.communityName}
          onCreated={handleRoomCreated}
          onClose={() => setCreateRoomFor(null)}
        />
      )}
      {showNewDm && (
        <NewDmModal
          onCreated={handleDmCreated}
          onClose={() => setShowNewDm(false)}
        />
      )}
    </>
  );
}
