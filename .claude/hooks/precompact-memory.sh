#!/bin/bash
# PreCompact hook: Extract learnings from session and save to CLAUDE.local.md
# Receives JSON on stdin with: transcript_path, cwd, session_id, etc.

set -e

# Parse input
INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path')
CWD=$(echo "$INPUT" | jq -r '.cwd')
MEMORY_FILE="$CWD/CLAUDE.local.md"

# Skip if no transcript
[ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ] && exit 0

# Extract conversation content (assistant messages with actual content)
CONTENT=$(jq -r '
  select(.type == "assistant" and .message.content)
  | .message.content[]
  | select(.type == "text")
  | .text
' "$TRANSCRIPT_PATH" 2>/dev/null | head -c 50000)

# Skip if minimal content
[ ${#CONTENT} -lt 500 ] && exit 0

# Use claude CLI to extract learnings (--print for non-interactive, haiku for speed/cost)
LEARNINGS=$(echo "$CONTENT" | claude --print --model haiku "Extract any project-specific learnings, patterns, or preferences from this session that should be remembered for future work in this codebase. Format as bullet points under relevant headers. Only include genuinely useful insights, not generic advice. If nothing notable, respond with exactly 'NONE'." 2>/dev/null || echo "NONE")

# Skip if nothing learned
[ "$LEARNINGS" = "NONE" ] && exit 0

# Append to memory file
{
  echo ""
  echo "## Session $(date +%Y-%m-%d)"
  echo "$LEARNINGS"
} >> "$MEMORY_FILE"

echo "Saved session learnings to CLAUDE.local.md"
