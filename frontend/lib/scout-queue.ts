// A conversation receipt. Work state and execution remain authoritative in Odoo.
export type ScoutState = "submitting" | "queued" | "running" | "review_required" | "completed" | "cancelled" | "failed";
export type ScoutReceipt = { id: number | null; state: ScoutState; revision: number; request_key: string; result: string | null };
const states: ScoutState[] = ["queued", "running", "review_required", "completed", "cancelled", "failed"];

export function scoutReceipt(previous: ScoutReceipt | null, type: string, data: Record<string, unknown>): ScoutReceipt | null {
  if (type === "scout.requested") {
    if (previous) return previous;
    return typeof data.request_key === "string" ? { id: null, state: "submitting", revision: -1, request_key: data.request_key, result: null } : null;
  }
  if (type !== "scout.work" || typeof data.id !== "number" || !Number.isSafeInteger(data.id) || data.id < 1
      || typeof data.revision !== "number" || !Number.isSafeInteger(data.revision) || data.revision < 0
      || !states.includes(data.state as ScoutState) || typeof data.request_key !== "string"
      || (data.result !== null && data.result !== undefined && (typeof data.result !== "string" || data.result.length > 20000))) return previous;
  if (previous && (previous.request_key !== data.request_key || previous.id !== null && previous.id !== data.id || previous.revision > data.revision)) return previous;
  return { id: data.id, revision: data.revision, state: data.state as ScoutState, request_key: data.request_key, result: typeof data.result === "string" ? data.result : null };
}
