# M2-D Runtime Lifecycle Worklog

> Status: IN PROGRESS
> Base: `develop@45b7c448d437df9ced5b5776f017a008376dabbb`
> Branch: `agent/m2-runtime-lifecycle`
> Release decision: **NO RELEASE**

## Scope

M2-D extends the existing `DeepSeekRuntime` production loop with:

- explicit lifecycle state and content-minimized events;
- transition validation against the frozen manifest;
- checkpoint handoff at critical states;
- Provider-before-call cancellation and final tool-cancellation semantics;
- step/token/cost/context/time budgets;
- deterministic tool-error continue/terminate policy;
- structured malformed-Provider boundaries supported by this slice;
- a focused M2-D gate.

## Exclusions

No second Agent loop, Workspace P1, CLI protocol, Provider streaming/retry, durable encrypted/locked checkpoint store, M3 Evidence redesign, packaging, `master`, tag, or release change.

## Entry evidence

- M2-C implementation merge: `7793a10152a49fb815aac667906080a4e1a39920`;
- M2-C docs closeout merge: `45b7c448d437df9ced5b5776f017a008376dabbb`;
- repository status: M0/M1/M2-A/M2-B/M2-C CLOSED, M2-D NEXT.
