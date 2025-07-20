#!/bin/bash

REPORT_FILE="model_review.md"
MODEL="ai/llama3.2:latest"

echo "# 🧠 LLM Code Review Summary" > $REPORT_FILE

# Ensure origin/main exists for diff
git fetch origin main

# Get list of modified files
FILES=$(git diff origin/main...HEAD --name-only --diff-filter=ACM | grep -E '\.py|\.js|\.ts|\.php|\.go$')

if [ -z "$FILES" ]; then
  echo "No changed files to review." >> $REPORT_FILE
else
  for FILE in $FILES; do
    if [ -f "$FILE" ]; then
      echo -e "\n## 🔍 $FILE" >> $REPORT_FILE
      CODE=$(cat "$FILE")

      PROMPT="Review this code and provide any improvements or suggestions:\n\n$CODE"
      RESPONSE=$(docker model run $MODEL "$PROMPT" 2>/dev/null)

      echo -e "$RESPONSE" >> $REPORT_FILE
    fi
  done
fi
