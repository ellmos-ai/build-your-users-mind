# Translation task — docs of `build-your-users-mind`

**For:** a translation agent (e.g. agy/Gemini)
**Repo root:** `<repo-root>`
**Source (authoritative):** the English root docs (`README.md`, `SKILL.md`, `TAXONOMY.md`,
`SOURCE-ADAPTERS.md`, `SECURITY.md`, `RELEASE_GATE.md`, `TODO.md`)
**Invocation note:** if the agent's stdout mangles CJK, have it **write the files directly** to disk
(do not return them over stdout).

## Task
Translate the English root docs into **5 target languages** and write them under `locales/<lang>/` (same
filenames):

| Language | Folder |
|---|---|
| German | `locales/de/` |
| Español | `locales/es/` |
| 日本語 | `locales/ja/` |
| Русский | `locales/ru/` |
| 中文 (simplified) | `locales/zh/` |

(English root docs stay unchanged and authoritative.)

## Rules
1. **Translate prose only.** Leave unchanged: Markdown structure, heading **anchors/links**, code blocks,
   table scaffolding, CLI flags, file names, topics.
2. **Do NOT translate proper nouns:** `build-your-users-mind`, `feedforward`, `feedback precognition`
   (term; a local gloss in parentheses is fine), file/folder names, the avatar file names.
3. **Tagline "what you mind is what you get"** stays in the English original (an optional local gloss in
   parentheses is fine).
4. **Genuine diacritics / native scripts** (ä ö ü ß, ñ, 漢字/かな, Cyrillic). No ASCII substitutes.
5. **Disclaimer as the first line** of every translation: a target-language rendering of
   `> English (README.md) is authoritative; this translation may lag.`
6. **Language-switcher row** in each `README.md` with correct relative paths to the sibling languages and root.
7. Tone: technical-precise, concise; do not add emojis.

## Result
The translated docs under `locales/<lang>/`, valid Markdown, same section order as the originals.
Then a short confirmation listing the files written (+ line count per file).
