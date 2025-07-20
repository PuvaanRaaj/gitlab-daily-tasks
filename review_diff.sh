#!/bin/bash

REPORT_FILE="model_review.md"
MODEL="ai/llama3.2:latest"

echo "# 🧠 LLM Code Review Summary" > "$REPORT_FILE"

# Get the latest commit SHA that actually modified tracked files
LATEST_COMMIT=$(git log --pretty=format:"%H" -n 1)

# Double check with HEAD^ to form diff range
PREV_COMMIT=$(git rev-parse "$LATEST_COMMIT"^)

# Get changed files from that specific commit
FILES=$(git diff --name-only --diff-filter=ACM "$PREV_COMMIT" "$LATEST_COMMIT" | grep -E '\.(py|js|ts|php|go|sh|md|ya?ml)$')

if [ -z "$FILES" ]; then
  echo "No relevant files changed in the last commit ($LATEST_COMMIT)."
  exit 0  # Don't proceed if nothing relevant changed
fi

echo "Files changed in last commit ($LATEST_COMMIT):"
echo "$FILES"

# Aggregate code for prompt
AGGREGATED_CODE=""
for FILE in $FILES; do
  if [ -f "$FILE" ]; then
    FILE_CONTENT=$(cat "$FILE")
    AGGREGATED_CODE+="\n\n### File: $FILE\n\`\`\`\n$FILE_CONTENT\n\`\`\`"
  fi
done

# AI prompt
PROMPT="You are an expert code reviewer. Review the following code files and provide detailed, actionable suggestions. Mention filenames, and include performance, security, and style feedback:\n$AGGREGATED_CODE"

# Run the model
RESPONSE=$(docker model run "$MODEL" "$PROMPT" 2>/dev/null)

# Write to review file
echo -e "$RESPONSE" >> "$REPORT_FILE"
