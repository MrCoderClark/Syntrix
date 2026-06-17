"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";

interface Props {
  slug: string;
}

export function JoinButton({ slug }: Props) {
  const [state, setState] = useState<
    "loading" | "guest" | "member" | "not_member"
  >("loading");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch(`/api/communities/${slug}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.is_member) setState("member");
        else if (data.detail === "Not authenticated") setState("guest");
        else setState("not_member");
      })
      .catch(() => setState("guest"));
  }, [slug]);

  async function toggle() {
    setBusy(true);
    const action = state === "member" ? "leave" : "join";
    const res = await fetch(`/api/communities/${slug}/${action}`, {
      method: "POST",
    });
    if (res.ok) {
      setState(action === "join" ? "member" : "not_member");
    }
    setBusy(false);
  }

  if (state === "loading" || state === "guest") return null;

  return (
    <Button
      variant={state === "member" ? "default" : "primary"}
      onClick={toggle}
      disabled={busy}
    >
      {state === "member" ? "Leave" : "Join"}
    </Button>
  );
}
