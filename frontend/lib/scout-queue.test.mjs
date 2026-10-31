import assert from "node:assert/strict";
import { test } from "node:test";
import { scoutReceipt } from "./scout-queue.ts";
import { applyEvent, emptyTranscript } from "./transcript.ts";

const item = (revision, state = "running", extra = {}) => ({ id: 17, request_key: "scout-owner-1", revision, state, result: null, ...extra });

test("receipt refresh never moves backwards or crosses requests", () => {
  const current = scoutReceipt(null, "scout.work", item(3));
  assert.equal(scoutReceipt(current, "scout.work", item(2)), current);
  assert.equal(scoutReceipt(current, "scout.work", item(4, "completed", { id: 18 })), current);
  assert.equal(scoutReceipt(current, "scout.work", item(4, "completed", { request_key: "other" })), current);
  assert.equal(scoutReceipt(current, "scout.work", item(4, "completed")).state, "completed");
});

test("reconnecting to a submitted task updates one card with its original turn", () => {
  let transcript = emptyTranscript();
  for (const event of [
    { seq: 1, type: "scout.requested", data: { request_key: "scout-owner-1" } },
    { seq: 2, type: "scout.work", data: item(1, "queued") },
    { seq: 3, type: "scout.work", data: item(3, "review_required", { result: "Draft" }) },
  ]) transcript = applyEvent(transcript, { ...event, turn_id: 9 });
  assert.equal(transcript.items.length, 1);
  assert.equal(transcript.items[0].turnId, 9);
  assert.equal(transcript.items[0].receipt.result, "Draft");
  const replay = applyEvent(transcript, { seq: 2, type: "scout.work", data: item(1), turn_id: 9 });
  assert.equal(replay, transcript);
});

test("invalid result and state cannot replace the last known receipt", () => {
  const current = scoutReceipt(null, "scout.work", item(3));
  for (const invalid of [item(4, "execute"), item(-1), item(4, "review_required", { result: {} }), item(4, "queued", { id: -1 })]) {
    assert.equal(scoutReceipt(current, "scout.work", invalid), current);
  }
});
