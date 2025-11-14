#!/usr/bin/env python3
"""
Create Project Issues for AI Scrum Cluster

This script breaks down a high-level project description into
individual GitHub issues ready for the distributed cluster to work on.

Usage:
    python create_project_issues.py --repo owner/repo-name --project "Build a calculator app"
    python create_project_issues.py --repo owner/repo-name --project-file project_description.txt
"""

import subprocess
import sys
import argparse
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def call_claude_for_task_breakdown(project_description: str) -> list:
    """
    Use Claude to break down a project into tasks

    Args:
        project_description: High-level project description

    Returns:
        List of task dictionaries
    """
    try:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found in environment")
            sys.exit(1)

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Break down the following project into individual, concrete tasks that can be worked on independently.

Project: {project_description}

For each task, provide:
1. A clear, actionable title
2. A detailed description of what needs to be done
3. Priority (High/Medium/Low)
4. Estimated complexity (Simple/Medium/Complex)
5. Any dependencies on other tasks

Format your response as a JSON array of task objects with these fields:
- title: string
- description: string
- priority: string ("High" | "Medium" | "Low")
- complexity: string ("Simple" | "Medium" | "Complex")
- dependencies: string (comma-separated task titles or "None")

Example:
[
  {{
    "title": "Setup project structure",
    "description": "Create initial project directory...",
    "priority": "High",
    "complexity": "Simple",
    "dependencies": "None"
  }}
]

Return ONLY the JSON array, no other text."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        response_text = response.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        tasks = json.loads(response_text)
        return tasks

    except ImportError:
        print("❌ anthropic package not installed")
        print("   Install: pip install anthropic")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        sys.exit(1)


def create_github_issue(repo: str, task: dict, add_ai_ready_label: bool = True) -> bool:
    """
    Create a GitHub issue for a task

    Args:
        repo: Repository in format "owner/repo"
        task: Task dictionary
        add_ai_ready_label: Whether to add 'ai-ready' label

    Returns:
        True if successful
    """
    title = task['title']
    description = task['description']
    priority = task.get('priority', 'Medium')
    complexity = task.get('complexity', 'Medium')
    dependencies = task.get('dependencies', 'None')

    # Create issue body
    body = f"{description}\n\n"
    body += f"**Priority:** {priority}\n"
    body += f"**Complexity:** {complexity}\n"
    body += f"**Dependencies:** {dependencies}\n"

    try:
        cmd = [
            "gh", "issue", "create",
            "--repo", repo,
            "--title", title,
            "--body", body
        ]

        if add_ai_ready_label:
            cmd.extend(["--label", "ai-ready"])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            issue_url = result.stdout.strip()
            print(f"  ✅ Created: {title}")
            print(f"     {issue_url}")
            return True
        else:
            print(f"  ❌ Failed: {title}")
            print(f"     {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Error creating issue: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create GitHub issues for a project using AI breakdown"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in format 'owner/repo'"
    )
    parser.add_argument(
        "--project",
        help="Project description (one-liner)"
    )
    parser.add_argument(
        "--project-file",
        help="Path to file containing project description"
    )
    parser.add_argument(
        "--no-ai-ready",
        action="store_true",
        help="Don't add 'ai-ready' label (issues won't be picked up by cluster)"
    )

    args = parser.parse_args()

    # Get project description
    if args.project:
        project_description = args.project
    elif args.project_file:
        project_file = Path(args.project_file)
        if not project_file.exists():
            print(f"❌ Project file not found: {project_file}")
            sys.exit(1)
        project_description = project_file.read_text()
    else:
        print("❌ Either --project or --project-file is required")
        sys.exit(1)

    print("==========================================")
    print("Creating Project Issues")
    print("==========================================")
    print(f"Repository: {args.repo}")
    print(f"Project: {project_description[:100]}...")
    print("")

    # Check if gh CLI is installed
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI (gh) is not installed")
        print("   Install: https://cli.github.com/")
        sys.exit(1)

    # Break down project into tasks
    print("🤖 Using Claude to break down project into tasks...")
    tasks = call_claude_for_task_breakdown(project_description)
    print(f"   Found {len(tasks)} tasks")
    print("")

    # Create GitHub issues
    print("📝 Creating GitHub issues...")
    add_ai_ready = not args.no_ai_ready

    successful = 0
    for i, task in enumerate(tasks, 1):
        print(f"\n{i}/{len(tasks)}: {task['title']}")
        if create_github_issue(args.repo, task, add_ai_ready):
            successful += 1

    print("")
    print("==========================================")
    print(f"✅ Created {successful}/{len(tasks)} issues")
    print("==========================================")
    print("")

    if add_ai_ready:
        print("Issues are labeled 'ai-ready' and will be picked up by the cluster.")
        print("Monitor progress:")
        print(f"  • Cluster status: curl http://192.168.100.200:8000/health")
        print(f"  • Queue status:   curl http://192.168.100.200:8000/queue")
        print(f"  • GitHub issues:  https://github.com/{args.repo}/issues")
    else:
        print("Issues created without 'ai-ready' label.")
        print("To queue them for the cluster, add the 'ai-ready' label manually.")

    print("")


if __name__ == "__main__":
    main()
