---
id: "0007"
title: "No auth or CSRF in the MVP; bind to 127.0.0.1 only"
status: proposed
date: 2026-10-17
decided_by: human
affects: ["web-app"]
supersedes: []
superseded_by: null
---
## Context
The MVP has no login, no CSRF tokens, and plain form POSTs. It is a local helper for one operator.

## Decision
The MVP ships without authentication and without CSRF protection, and the server must bind to
127.0.0.1 only. Any network exposure (LAN, tunnel, public host) or any capability that could
trigger deployments or rewrite project state requires revisiting this ADR first: auth and CSRF
protection land before exposure.

## Reasons
- A local MVP for one operator on a trusted machine has a real attacker surface of ~zero.
- Building auth now would be speculative invention before a deployment target exists.

## Alternatives rejected
- Session login from day one: complexity with no adversary yet.
- Bearer tokens per device: overkill before remote use is planned.

## Consequences
- Never run the server on 0.0.0.0 or behind a tunnel before this ADR is superseded.
- The README and `/` docs must state the local-only assumption.
- Deployment-driving features are blocked by this ADR until it is superseded.
## Summary (العربية)
النسخة الأولى بدون تسجيل دخول وبدون حماية CSRF، وربط الخادم بـ 127.0.0.1 فقط. مراجعة وملپة
القرار قبل أي تعرض للشبكة أو قبل السماح للمصنع بإطلاق نشر.
