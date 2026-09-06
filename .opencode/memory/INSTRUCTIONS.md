# Two-Tier Memory System — Instructions

**Project**: extrator-proprietarios  
**Memory Dir**: `.opencode/memory/`  
**Auto-load**: This file + `MEMORY.md` are loaded at session start via opencode config.

---

## Tier 1 — Always-Loaded Index (MEMORY.md + topic files)

### Structure
```
.opencode/memory/
├── INSTRUCTIONS.md    ← This file (rules)
├── MEMORY.md          ← Index: one line per fact, links to topic file
└── <slug>.md          ← Topic files with frontmatter
```

### Topic File Frontmatter
```markdown
---
name: kebab-case-slug
description: one-line summary — used to judge relevance in a future session
metadata:
  type: feedback | architecture | business-rule | reference
---
```

---

## Admission Test — Save Only If YES

> **Would a future session be surprised and grateful to know this BEFORE starting, rather than discovering it the hard way?**

### DO NOT SAVE
- Derivable by reading code or git history
- Deadlines, motivations, anything temporary to right now
- Debugging recipes (belongs in commit messages)
- Anything a 5-minute grep would reveal

### DO SAVE
- A mistake a session made that had to be corrected
- An architecture pattern found only after failed attempts
- A business rule invisible in the code
- Where to find something outside the repo (dashboard, wiki, channel)
- Non-obvious constraints, gotchas, or "why this way" decisions

**Err toward not saving.** A memory nobody needed is clutter; a lesson relearned the hard way is expensive — but a small, high-signal index beats a large, ignored one every time.

---

## Growth Policy — Cap at ~130 Non-Blank Lines

**Before adding a new entry:**
1. Count non-blank lines in `MEMORY.md`
2. If ≥ 130, sanitize first:
   - Score each entry: recency × specificity × likelihood of preventing a real future mistake
   - For each low-scoring entry, migrate to Tier 2 in exact order:
     1. **Dedup** — search Tier 2 for same topic; extend existing note
     2. **Match target template** — Tier 2 may have required structure
     3. **Create** note in Tier 2
     4. **Confirm** — read it back. No successful read = no deletion
     5. **Only then** delete from index and topic file
3. Rewrite index with remaining entries
4. Add new entry

**Deleting before read-back confirms = data loss, not cleanup.** If unsure, leave it — migrating later costs nothing.

---

## Tier 2 — Long-Term Store

**Destination**: `docs/superpowers/memory/` (project docs folder)  
**Access**: Direct file edit / `read` tool  
**Format**: Same frontmatter + full context

Migrate low-value entries here. They persist but don't load every session.

---

## Adding a Memory (Workflow)

```bash
# 1. Create topic file
cat > .opencode/memory/my-topic.md << 'EOF'
---
name: my-topic
description: One-line summary for relevance judgment
metadata:
  type: architecture
---
## Context
[Full details here]
EOF

# 2. Add line to MEMORY.md
echo "- [my-topic](my-topic.md) — One-line summary" >> .opencode/memory/MEMORY.md

# 3. Verify line count
wc -l .opencode/memory/MEMORY.md
```

---

## Session Start Protocol

At session start, the agent MUST:
1. Read `.opencode/memory/INSTRUCTIONS.md`
2. Read `.opencode/memory/MEMORY.md`
3. Scan descriptions for relevance to current task
4. Read relevant topic files (not all)
5. Proceed with task using this context

---

## Configuration for Auto-Load

Add to `.opencode/opencode.json` (create if needed):
```json
{
  "memory": {
    "autoLoad": [
      ".opencode/memory/INSTRUCTIONS.md",
      ".opencode/memory/MEMORY.md"
    ]
  }
}
```