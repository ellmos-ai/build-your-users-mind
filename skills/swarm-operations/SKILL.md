---
name: swarm-operations
description: Coordination strategies for AI agents working in parallel or hierarchically — 5 multi-agent patterns (Epstein, Hierarchy, Stigmergy, Consensus, Specialist). Bundled dependency of build-your-users-mind; its stage-2 classification uses Hierarchy + Stigmergy.
---

# Swarm Operations: 5 patterns for multi-agent systems

Coordination strategies for AI agents working in parallel or hierarchically —
from simple task distribution to emergent swarm patterns.

> Bundled dependency of **build-your-users-mind**. The module's stage-2 classification uses
> pattern **2 (Hierarchy)** + pattern **3 (Stigmergy)**: domain leads direct chunk workers, and
> agents coordinate through shared files rather than direct messaging.

---

## Overview of the 5 patterns

| # | Pattern | Agents | Coordination | Best for |
|---|---------|--------|-------------|----------|
| 1 | Epstein method | 3-5 | Central (orchestrator) | Knowledge building, research |
| 2 | Hierarchy swarm | 5-20 | Tree structure | Large projects, refactoring |
| 3 | Stigmergy | 3-10 | Decentralized (environment) | Exploration, data crawling |
| 4 | Consensus | 3-7 | Peer-to-peer | Decisions, review |
| 5 | Specialist swarm | 3-8 | Hub-and-spoke | Cross-domain |

---

## Pattern 1: Epstein method
**Principle:** one orchestrator distributes subtasks to specialized workers; results are collected,
deduplicated and merged into a whole.
**Roles:** Orchestrator (split, distribute, synthesize) · Worker (handle subtask, return structured result)
· Validator (optional, quality/consistency check).
**Use when:** research with several independent aspects, knowledge building, multi-source extraction.
**Limits:** orchestrator is a single point of failure; overhead below 3 subtasks; dependent subtasks hard to parallelize.

## Pattern 2: Hierarchy swarm
**Principle:** tree of boss nodes coordinating sub-teams; each boss knows only its direct reports.
**Levels:** Project boss (overall plan, final result) · Team lead (coordinate a subarea) · Worker (single task).
**Implementation:** decompose into 2-4 areas → one lead per area → leads assign workers → aggregate bottom-up (worker → lead → boss).
**Use when:** large projects (>10 files), refactoring across modules, documenting whole systems, natural hierarchy.
**Limits:** cross-level communication overhead; the big picture can be lost at lower levels; needs ≥5 agents to pay off.

## Pattern 3: Stigmergy (environment coordination)
**Principle:** agents do NOT communicate directly but via the environment (shared state) — like ants leaving pheromones.
**Mechanisms:** filesystem (result JSONs in a shared folder), database (shared table/queue), message queue (pub/sub),
marker files (`.done`/`.lock`).
**Implementation:** define a shared folder → naming convention → status markers (how an agent signals "done") →
conflict avoidance (each agent writes only its own files) → an aggregator collects everything at the end.
**Use when:** exploration (crawling, code analysis), loosely coupled tasks, when direct agent communication isn't possible, robustness over speed.
**Limits:** no real-time coordination; write conflicts; harder to debug (distributed state).

## Pattern 4: Consensus
**Principle:** several agents solve the SAME task independently; results are compared and a consensus is formed.
**Strategies:** majority vote (facts) · best-of-N (quality score, creative tasks) · synthesis (combine elements) · debate (agents critique each other).
**Implementation:** same task to N agents → collect all answers → compare agreements/divergences → form consensus → determine confidence (3/3 = high, 2/3 = medium).
**Use when:** critical decisions (security/architecture review), code review (multiple perspectives), fact verification, when a single agent could be unreliable.
**Limits:** N× cost/time; all agents can make the same mistake; consensus ≠ correctness.

## Pattern 5: Specialist swarm
**Principle:** each agent is an expert for one domain; a coordinator routes tasks to the right specialist.
**Roles:** Coordinator (routing logic, overview of all domains) · Domain experts (deep, domain-specific knowledge/tools/prompts).
**Implementation:** define domains → create one expert per domain → routing logic → handoffs for cross-domain tasks → coordinator integrates partial results.
**Use when:** cross-domain projects, distinct expertise areas needed, support systems, complex systems with clearly separable modules.
**Limits:** routing errors; cross-cutting tasks hard to assign; overhead with few domains.

---

## Comparison

| Criterion | Epstein | Hierarchy | Stigmergy | Consensus | Specialist |
|-----------|---------|-----------|-----------|-----------|------------|
| Complexity | Low | High | Medium | Low | Medium |
| Min. agents | 3 | 5 | 3 | 3 | 3 |
| Coordination | Central | Tree | Decentral | Peer | Hub-spoke |
| Fault tolerance | Low | Medium | High | High | Medium |
| Scalability | Medium | High | High | Low | Medium |
| Overhead | Low | High | Low | High (N×) | Medium |

---

## General principles
1. **Task decomposition:** tasks must be **independent** to parallelize; dependent tasks run sequentially or with explicit waits; pick the right granularity (not too fine = overhead, not too coarse = no benefit).
2. **Result aggregation:** fix a format (JSON, Markdown, structured dicts); deduplicate; resolve conflicts.
3. **Error handling:** timeout per agent (5-10 min); retry on transient errors; fallback (can the orchestrator take over?); partial results beat none.
4. **Communication:** clear input/output interfaces; minimal coupling; idempotency (same input → same output) for retry safety.
5. **Monitoring:** status tracking (started/running/done/failed); progress measurement; logging per agent.

## Decision guide
```
1. Decomposable into independent parts?  YES → how many?  3-5 → Epstein · 5-20 → Hierarchy
2. Same task, multiple perspectives?     YES → Consensus
3. Distinct expertise areas needed?      YES → Specialist swarm
4. Loosely coupled exploration?          YES → Stigmergy
5. Otherwise a single agent is probably enough.
```

*Adapted from the author's swarm-operations skill (BACH lineage), bundled here for build-your-users-mind.*
