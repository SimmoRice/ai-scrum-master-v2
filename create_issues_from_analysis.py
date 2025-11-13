#!/usr/bin/env python3
"""
Create GitHub issues from project analysis
"""

import subprocess
import re
import sys
from pathlib import Path

# ANSI color codes
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color


def parse_tasks_from_markdown(analysis_file: Path):
    """Parse tasks from the analysis markdown file"""

    with open(analysis_file, 'r') as f:
        content = f.read()

    tasks = []

    # Split by task headers (### **Task N:)
    task_pattern = r'### \*\*Task \d+: (.+?)\*\*\n- \*\*Description\*\*: (.+?)\n- \*\*Priority\*\*: (.+?)\n- \*\*Complexity\*\*: (.+?)\n- \*\*Category\*\*: (.+?)(?:\n- \*\*Dependencies\*\*: (.+?))?(?:\n---|\Z)'

    matches = re.findall(task_pattern, content, re.DOTALL)

    for match in matches:
        title = match[0].strip()
        description = match[1].strip()
        priority = match[2].strip()
        complexity = match[3].strip()
        category = match[4].strip()
        dependencies = match[5].strip() if match[5] else "None"

        tasks.append({
            'title': title,
            'description': description,
            'priority': priority,
            'complexity': complexity,
            'category': category,
            'dependencies': dependencies
        })

    return tasks


def create_github_issue(repo: str, task: dict) -> bool:
    """Create a single GitHub issue"""

    title = task['title']
    priority = task['priority']
    complexity = task['complexity']
    category = task['category']
    dependencies = task['dependencies']
    description = task['description']

    # Create issue body
    body = f"{description}\n\n"
    body += f"**Priority:** {priority}\n"
    body += f"**Complexity:** {complexity}\n"
    body += f"**Category:** {category}\n"
    body += f"**Dependencies:** {dependencies}\n"

    try:
        result = subprocess.run(
            ["gh", "issue", "create",
             "--repo", repo,
             "--title", title,
             "--body", body],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path.home() / "Development/repos/ai-hedge-fund"
        )

        if result.returncode == 0:
            # Extract issue number from output
            issue_url = result.stdout.strip()
            print(f"{GREEN}✅ Created: #{issue_url.split('/')[-1]} - {title}{NC}")
            return True
        else:
            print(f"{RED}❌ Failed to create '{title}': {result.stderr}{NC}")
            return False

    except Exception as e:
        print(f"{RED}❌ Error creating issue '{title}': {e}{NC}")
        return False


def main():
    analysis_file = Path("project_analysis.md")

    if not analysis_file.exists():
        print(f"{RED}❌ Analysis file not found: {analysis_file}{NC}")
        print(f"Run: python analyze_project.py ~/Development/repos/ai-hedge-fund")
        sys.exit(1)

    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}📝 Creating GitHub Issues from Analysis{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

    # Parse tasks
    print(f"{BLUE}📋 Parsing tasks from {analysis_file}...{NC}\n")
    tasks = parse_tasks_from_markdown(analysis_file)

    if not tasks:
        print(f"{RED}❌ No tasks found in analysis file{NC}")
        sys.exit(1)

    print(f"{GREEN}Found {len(tasks)} tasks{NC}\n")

    # Get repository info
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner"],
            cwd=Path.home() / "Development/repos/ai-hedge-fund",
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            import json
            repo_data = json.loads(result.stdout)
            repo = repo_data['nameWithOwner']
            print(f"{BLUE}Repository: {repo}{NC}\n")
        else:
            print(f"{RED}❌ Could not determine repository{NC}")
            sys.exit(1)
    except Exception as e:
        print(f"{RED}❌ Error getting repository info: {e}{NC}")
        sys.exit(1)

    # Confirm with user
    print(f"{YELLOW}About to create {len(tasks)} issues in {repo}{NC}")
    response = input(f"Continue? [y/N]: ")

    if response.lower() != 'y':
        print(f"{YELLOW}Cancelled{NC}")
        sys.exit(0)

    print()

    # Create issues
    created = 0
    failed = 0

    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] ", end='')
        if create_github_issue(repo, task):
            created += 1
        else:
            failed += 1

    # Summary
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{GREEN}✅ Created: {created} issues{NC}")
    if failed > 0:
        print(f"{RED}❌ Failed: {failed} issues{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

    print(f"{GREEN}View issues at: https://github.com/{repo}/issues{NC}\n")


if __name__ == "__main__":
    main()
