#!/usr/bin/env python3
"""
Project Analyzer - Analysis-only mode for AI Scrum Master

Analyzes a codebase and creates GitHub issues with recommendations
without implementing any changes.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ANSI color codes
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color


def analyze_codebase(project_path: Path) -> str:
    """
    Use Claude to analyze the codebase and provide recommendations

    Args:
        project_path: Path to the project to analyze

    Returns:
        Analysis results as markdown
    """
    print(f"{BLUE}🔍 Analyzing codebase at {project_path}...{NC}")

    # Get directory structure
    try:
        tree_output = subprocess.run(
            ["find", str(project_path), "-type", "f", "-not", "-path", "*/.*", "-not", "-path", "*/node_modules/*", "-not", "-path", "*/__pycache__/*"],
            capture_output=True,
            text=True,
            timeout=10
        ).stdout

        # Limit to first 200 files
        files = tree_output.strip().split('\n')[:200]
        file_tree = '\n'.join(files)
    except Exception as e:
        print(f"{YELLOW}⚠️  Could not generate file tree: {e}{NC}")
        file_tree = "Unable to generate file tree"

    # Read key files
    key_files = ['README.md', 'package.json', 'requirements.txt', 'setup.py', 'Cargo.toml', 'go.mod', 'pom.xml']
    file_contents = {}

    for filename in key_files:
        file_path = project_path / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    file_contents[filename] = f.read()[:2000]  # First 2000 chars
            except Exception as e:
                print(f"{YELLOW}⚠️  Could not read {filename}: {e}{NC}")

    # Create analysis prompt
    prompt = f"""You are analyzing a software project for improvement opportunities.

Project structure:
```
{file_tree}
```

Key files content:
"""

    for filename, content in file_contents.items():
        prompt += f"\n\n{filename}:\n```\n{content}\n```"

    prompt += """

Please analyze this project and provide:

1. **Project Overview**: What is this project? What does it do?

2. **Architecture Analysis**:
   - Current architecture/structure
   - Technology stack
   - Key components

3. **Improvement Recommendations**: Specific, actionable improvements organized by category:
   - Code Quality (refactoring, standards, best practices)
   - Testing (unit tests, integration tests, coverage)
   - Security (vulnerabilities, authentication, data protection)
   - Performance (optimization opportunities)
   - Documentation (missing docs, outdated docs)
   - DevOps/CI/CD (automation, deployment)
   - Features (missing functionality, enhancements)

4. **Task Breakdown**: For each recommendation, provide:
   - **Title**: Brief, specific task title
   - **Description**: What needs to be done
   - **Priority**: High/Medium/Low
   - **Complexity**: Small/Medium/Large
   - **Category**: One of the categories above
   - **Dependencies**: Any tasks that must be completed first

Format the output as structured markdown that can be easily parsed into GitHub issues.
Each task should be clearly separated and labeled.
"""

    # Call Claude
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    print(f"{BLUE}🤖 Consulting Claude for analysis...{NC}")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    analysis = response.content[0].text

    print(f"{GREEN}✅ Analysis complete!{NC}\n")

    return analysis


def parse_tasks_from_analysis(analysis: str) -> List[Dict[str, str]]:
    """
    Parse tasks from the analysis markdown

    Args:
        analysis: Analysis markdown from Claude

    Returns:
        List of task dictionaries
    """
    tasks = []

    # Simple parsing - look for task sections
    # This is a basic implementation - could be enhanced with regex or LLM parsing
    lines = analysis.split('\n')
    current_task = {}

    for line in lines:
        line = line.strip()

        # Look for task markers
        if line.startswith('**Title**:') or line.startswith('- **Title**:'):
            if current_task:
                tasks.append(current_task)
            current_task = {'title': line.split(':', 1)[1].strip()}
        elif line.startswith('**Description**:') or line.startswith('- **Description**:'):
            current_task['description'] = line.split(':', 1)[1].strip()
        elif line.startswith('**Priority**:') or line.startswith('- **Priority**:'):
            current_task['priority'] = line.split(':', 1)[1].strip()
        elif line.startswith('**Complexity**:') or line.startswith('- **Complexity**:'):
            current_task['complexity'] = line.split(':', 1)[1].strip()
        elif line.startswith('**Category**:') or line.startswith('- **Category**:'):
            current_task['category'] = line.split(':', 1)[1].strip()

    if current_task:
        tasks.append(current_task)

    return tasks


def create_github_issues(repo: str, tasks: List[Dict[str, str]], dry_run: bool = True):
    """
    Create GitHub issues from parsed tasks

    Args:
        repo: Repository in format 'owner/repo'
        tasks: List of task dictionaries
        dry_run: If True, just print what would be created
    """
    if dry_run:
        print(f"\n{YELLOW}📋 DRY RUN - Would create the following issues:{NC}\n")

        for i, task in enumerate(tasks, 1):
            title = task.get('title', 'Untitled')
            priority = task.get('priority', 'Medium')
            complexity = task.get('complexity', 'Medium')
            category = task.get('category', 'General')

            print(f"{i}. [{priority}] {title}")
            print(f"   Category: {category} | Complexity: {complexity}")
            print()
    else:
        print(f"\n{BLUE}📝 Creating GitHub issues in {repo}...{NC}\n")

        for task in tasks:
            title = task.get('title', 'Untitled')
            description = task.get('description', 'No description')
            priority = task.get('priority', 'Medium').lower()
            complexity = task.get('complexity', 'Medium').lower()
            category = task.get('category', 'General').lower()

            # Create issue body
            body = f"{description}\n\n"
            body += f"**Priority:** {priority}\n"
            body += f"**Complexity:** {complexity}\n"
            body += f"**Category:** {category}\n"

            # Create labels
            labels = [f"priority:{priority}", f"complexity:{complexity}", category]

            # Create issue using gh CLI
            try:
                result = subprocess.run(
                    ["gh", "issue", "create",
                     "--repo", repo,
                     "--title", title,
                     "--body", body,
                     "--label", ",".join(labels)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    print(f"{GREEN}✅ Created: {title}{NC}")
                else:
                    print(f"{RED}❌ Failed to create '{title}': {result.stderr}{NC}")

            except Exception as e:
                print(f"{RED}❌ Error creating issue '{title}': {e}{NC}")


def main():
    if len(sys.argv) < 2:
        print(f"{RED}Usage: python analyze_project.py <project_path> [--create-issues]{NC}")
        print(f"\nExample:")
        print(f"  python analyze_project.py ~/Development/repos/ai-hedge-fund")
        print(f"  python analyze_project.py ~/Development/repos/ai-hedge-fund --create-issues")
        sys.exit(1)

    project_path = Path(sys.argv[1]).expanduser().resolve()
    create_issues = '--create-issues' in sys.argv

    if not project_path.exists():
        print(f"{RED}❌ Error: Project path does not exist: {project_path}{NC}")
        sys.exit(1)

    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}🔍 AI Scrum Master - Project Analyzer{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    print(f"Project: {project_path}")
    print(f"Mode: {'Create GitHub Issues' if create_issues else 'Analysis Only (Dry Run)'}")
    print()

    # Analyze codebase
    analysis = analyze_codebase(project_path)

    # Save analysis to file
    analysis_file = Path("project_analysis.md")
    with open(analysis_file, 'w') as f:
        f.write(analysis)

    print(f"{GREEN}📄 Analysis saved to: {analysis_file}{NC}\n")

    # Parse tasks
    print(f"{BLUE}📋 Parsing recommendations into tasks...{NC}\n")
    tasks = parse_tasks_from_analysis(analysis)

    if not tasks:
        print(f"{YELLOW}⚠️  No structured tasks found in analysis.{NC}")
        print(f"{YELLOW}Please review {analysis_file} for recommendations.{NC}")
        return

    print(f"{GREEN}Found {len(tasks)} actionable tasks{NC}\n")

    # Get repository info
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            import json
            repo_data = json.loads(result.stdout)
            repo = repo_data['nameWithOwner']
        else:
            print(f"{RED}❌ Could not determine repository. Make sure you're in a GitHub repo.{NC}")
            return
    except Exception as e:
        print(f"{RED}❌ Error getting repository info: {e}{NC}")
        return

    # Create issues
    create_github_issues(repo, tasks, dry_run=not create_issues)

    if not create_issues:
        print(f"\n{YELLOW}💡 To create these issues in GitHub, run:{NC}")
        print(f"   python analyze_project.py {project_path} --create-issues")

    print(f"\n{GREEN}✅ Done!{NC}\n")


if __name__ == "__main__":
    main()
