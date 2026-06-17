# templates/commands/ — Optional command entry points (nuances of the loop)

These are **optional, agnostic command templates** that expose the `START.md` 0→4 loop at three
depths plus an orchestrator. They are a convenience layer on top of the avatar files — the loop works
without them, but giving the agent named entry points makes the nuances explicit and composable.

Copy them into your agent's command/prompt directory and replace the placeholders:
`<USER>` → your user, `<AGENT>` → your agent, `<AVATAR_DIR>` → where your avatar files live,
`<SKILL>` → the name you bound the module under (if any).

| Command | Loop depth | Side effect | Logs (3)? | Role |
|---|---|---|---|---|
| `read-my-mind` | 0→2 | no | no | diagnosis: predict what the user wants |
| `decide-like-me` | 0→2 | no | no | a single decision (workflow component) |
| `be-my-avatar` | 0→4 | yes (reversible only) | yes | act in the user's name (component/persona) |
| `avatar-orchestrator` | 0→4 ×N | yes (reversible only) | yes | autonomous chain over many decisions |

`decide-like-me` and `be-my-avatar` are designed to be **workflow components**: the first returns a
decision with no side effect, the second executes it (reversible + within pattern only). The
orchestrator chains `read-my-mind → decide-like-me → be-my-avatar` per pending item and bundles all
🔴/irreversible items into a single question to the user instead of guessing one by one.

> Platform note: in Claude Code these become `~/.claude/commands/*.md`; for Codex/Gemini/Kimi adapt
> to that agent's prompt/command mechanism. English is authoritative; templates are not translated.
