#!/bin/bash
REPORT_FILE="model_review.md"
MODEL="ai/llama3.2:latest"
echo "# LLM Code Review Summary" > "$REPORT_FILE"
# Get the latest commit SHA that actually modified tracked files
LATEST_COMMIT=$(git log --pretty=format:"%H" -n 1)
# Double check with HEAD^ to form diff range
PREV_COMMIT=$(git rev-parse "$LATEST_COMMIT"^)
# Get changed files from that specific commit
FILES=$(git diff --name-only --diff-filter=ACM "$PREV_COMMIT" "$LATEST_COMMIT" | grep -E '\.(py|js|ts|php|go|sh|md|ya?ml)$')
if [ -z "$FILES" ]; then
echo "No relevant files changed in the last commit ($LATEST_COMMIT)."
exit 0 # Don't proceed if nothing relevant changed
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
# Enhanced AI prompt
PROMPT="You are a senior software engineer conducting a thorough code review. Analyze the following code changes and provide a comprehensive review report.

## Review Guidelines:
- Focus on **specific, actionable feedback** with clear examples
- Prioritize critical issues (security, bugs, performance) over style preferences
- Reference specific **line numbers and filenames** when possible
- Suggest concrete improvements with code examples
- Consider maintainability, readability, and best practices

## Review Areas:
1. **Security**: Identify vulnerabilities, injection risks, authentication issues
2. **Bugs & Logic**: Spot potential runtime errors, edge cases, logic flaws
3. **Performance**: Highlight inefficiencies, memory leaks, optimization opportunities
4. **Architecture**: Assess code structure, design patterns, modularity
5. **Readability**: Comment on clarity, naming conventions, documentation
6. **Testing**: Evaluate test coverage, test quality, missing test cases
7. **Maintainability**: Consider future extensibility and refactoring needs

## Output Format:
For each file, provide:
- **Summary**: Brief overview of changes and overall quality
- **Critical Issues**: High-priority problems requiring immediate attention
- **Suggestions**: Specific improvements with code examples where helpful
- **Positive Notes**: Highlight good practices and well-written sections

## Code to Review:
$AGGREGATED_CODE

Please provide a detailed, professional review focusing on the most impactful improvements."

# Run the model
RESPONSE=$(docker model run "$MODEL" "$PROMPT" 2>/dev/null)

# Write to review file
echo -e "$RESPONSE" >> "$REPORT_FILE"