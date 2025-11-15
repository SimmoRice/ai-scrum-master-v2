#!/bin/bash
# View detailed user story specifications for issues

REPO="${1:-SimmoRice/taskmaster-app}"
ISSUE_NUM="${2}"

if [ -n "$ISSUE_NUM" ]; then
    # View single issue
    echo "=========================================="
    gh issue view "$ISSUE_NUM" --repo "$REPO" --json number,title,labels,body --jq '
        "Issue #\(.number): \(.title)",
        "Labels: \(.labels | map(.name) | join(", "))",
        "==========================================",
        "",
        .body,
        ""
    '
else
    # View all Phase 1 issues (1-5)
    for i in 1 2 3 4 5; do
        echo "=========================================="
        gh issue view "$i" --repo "$REPO" --json number,title,labels,body --jq '
            "Issue #\(.number): \(.title)",
            "Labels: \(.labels | map(.name) | join(", "))",
            "==========================================",
            "",
            .body,
            ""
        '
        echo ""
        echo ""
    done
fi
