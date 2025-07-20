#!/bin/bash

REPORT_FILE="model_review.md"
MODEL="ai/llama3.2:latest"

echo "# 🧠 LLM Code Review Summary" > "$REPORT_FILE"

# Get all changed source code files since the last push
FILES=$(git diff --name-only --diff-filter=ACM @{u}..HEAD | grep -E '\.py$|\.js$|\.ts$|\.php$|\.go$')

if [ -z "$FILES" ]; then
  echo "No relevant files changed since last push." >> "$REPORT_FILE"
  exit 0
fi

echo "Files changed since last push:"
echo "$FILES"

# Aggregate all code with filenames
AGGREGATED_CODE=""
for FILE in $FILES; do
  if [ -f "$FILE" ]; then
    FILE_CONTENT=$(cat "$FILE")
    AGGREGATED_CODE+="\n\n### File: $FILE\n\`\`\`\n$FILE_CONTENT\n\`\`\`"
  fi
done

# Prompt the LLM to review all files in one go
PROMPT="You are an expert code reviewer. Analyze the following code files and provide detailed suggestions, improvements, and flag any bad practices, security issues, or inefficiencies. Mention the filename when referring to specific code:\n$AGGREGATED_CODE"

RESPONSE=$(docker model run "$MODEL" "$PROMPT" 2>/dev/null)

# Save output
echo -e "$RESPONSE" >> "$REPORT_FILE"
