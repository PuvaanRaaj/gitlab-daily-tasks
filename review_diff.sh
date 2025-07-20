#!/bin/bash

REPORT_FILE="model_review.md"
MODEL="ai/llama3.2:latest"
BASE_BRANCH="${GITHUB_BASE_REF:-main}"

git fetch origin $BASE_BRANCH:refs/remotes/origin/$BASE_BRANCH

echo "# LLM Code Review Summary" > $REPORT_FILE

FILES=$(git diff origin/$BASE_BRANCH...HEAD --name-only --diff-filter=ACM | grep -E '\.py|\.js|\.ts|\.php|\.go$')

if [ -z "$FILES" ]; then
  echo " No changed files to review." >> $REPORT_FILE
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
