"use client";

import { useState } from "react";
import { scoutQueueAction } from "@/lib/api";
import { scoutReceipt, type ScoutReceipt } from "@/lib/scout-queue";
import type { TranscriptItem } from "@/lib/transcript";
import { Button } from "@/components/ui/Button";
import { Banner } from "@/components/ui/Banner";

const labels = { submitting: "Submission receipt pending", queued: "Queued", running: "Working", review_required: "Review required", completed: "Accepted", cancelled: "Cancelled", failed: "Needs attention" };

export function ScoutWorkCard({ item, threadId, running }: {
  item: Extract<TranscriptItem, { kind: "scout_work" }>; threadId: number | null; running: boolean;
}) {
  const [local, setLocal] = useState<ScoutReceipt | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const receipt = local && local.revision >= item.receipt.revision ? local : item.receipt;
  async function act(action: "refresh" | "recover" | "accept" | "cancel") {
    if (threadId === null) return;
    setBusy(true); setError(null);
    try {
      const data = await scoutQueueAction(threadId, item.turnId, action, receipt.revision >= 0 ? receipt.revision : undefined);
      setLocal(scoutReceipt(receipt, "scout.work", data));
    } catch (err) { setError(err instanceof Error ? err.message : "The task receipt could not be read. Try refreshing it."); }
    finally { setBusy(false); }
  }
  return <section className="my-3 space-y-3 rounded-card border border-line bg-raised p-4" aria-label="Scout draft task">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <span className="font-medium">{receipt.id === null ? "Draft task" : `Draft task #${receipt.id}`}</span>
      <span role="status" className="text-sm text-muted">{labels[receipt.state]}</span>
    </div>
    {receipt.state === "review_required" && <p className="text-sm text-muted">{receipt.result ? "Review the returned draft before accepting it. Acceptance records your review." : "This task needs review before another attempt. No completed draft is available."}</p>}
    {receipt.result && <details><summary className="cursor-pointer text-sm">Read draft</summary><p className="mt-2 whitespace-pre-wrap text-sm">{receipt.result}</p></details>}
    {error && <Banner tone="danger">{error}</Banner>}
    <div className="flex flex-wrap gap-2">
      {receipt.id !== null && <Button size="sm" disabled={busy || threadId === null} onClick={() => void act("refresh")}>Refresh status</Button>}
      {receipt.id === null && !running && <Button size="sm" disabled={busy || threadId === null} onClick={() => void act("recover")}>Recover submission</Button>}
      {receipt.state === "review_required" && receipt.result && <Button size="sm" variant="primary" disabled={busy || threadId === null} onClick={() => void act("accept")}>Accept draft</Button>}
      {receipt.id !== null && ["queued", "running", "review_required", "failed"].includes(receipt.state) && <Button size="sm" disabled={busy || threadId === null} onClick={() => void act("cancel")}>Cancel task</Button>}
    </div>
  </section>;
}
