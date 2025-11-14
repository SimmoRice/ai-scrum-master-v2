#!/usr/bin/env python3
"""
Create GitHub Issue from User Story with AI Enhancement

This script:
1. Takes a basic user story from the user
2. Uses AI to ask clarifying questions
3. Expands the user story into a detailed GitHub issue
4. Creates the issue in the specified repository

Usage:
    python create_github_issue.py --repo ~/path/to/repo
    python create_github_issue.py --repo ~/path/to/repo --story "Add dark mode"
    python create_github_issue.py --repo ~/path/to/repo --interactive
"""

import subprocess
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from setup_github_repo import (
    check_gh_cli,
    check_if_git_repo,
    init_git_repo,
    check_git_remote,
    create_github_repo,
    enable_issues,
    create_labels
)


def call_claude_api(prompt: str, system_prompt: str = None) -> str:
    """
    Call Claude API to enhance user story

    Args:
        prompt: The prompt to send to Claude
        system_prompt: Optional system prompt

    Returns:
        Claude's response text
    """
    try:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found in environment")
            print("   Create a .env file with: ANTHROPIC_API_KEY=your_key")
            sys.exit(1)

        client = anthropic.Anthropic(api_key=api_key)

        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)

        return response.content[0].text

    except ImportError:
        print("❌ anthropic package not installed")
        print("   Install: pip install anthropic")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        sys.exit(1)


def ask_clarifying_questions(user_story: str, repo_context: Dict[str, Any]) -> str:
    """
    Use AI to generate and ask clarifying questions about the user story

    Args:
        user_story: The initial user story
        repo_context: Context about the repository (language, framework, etc.)

    Returns:
        Enhanced user story with user's answers
    """
    system_prompt = """You are a Product Owner helping to refine user stories into detailed requirements.

Your job is to ask 3-5 clarifying questions that will help create a comprehensive GitHub issue for an AI agent to implement.

Consider:
- What are the specific requirements?
- What constraints should be followed?
- What should NOT be changed?
- What are the acceptance criteria?
- Are there any technical preferences?
- What priority/complexity is this?

Ask focused, specific questions that will yield actionable details."""

    prompt = f"""User Story:
{user_story}

Repository Context:
- Path: {repo_context.get('path')}
- Type: {repo_context.get('type', 'Unknown')}

Generate 3-5 clarifying questions to help create a detailed implementation issue.
Format each question on a new line starting with "Q:"."""

    print("\n🤔 Analyzing user story and generating clarifying questions...")
    questions = call_claude_api(prompt, system_prompt)

    print("\n" + "="*60)
    print("📋 CLARIFYING QUESTIONS")
    print("="*60)
    print(questions)
    print("="*60)

    # Collect answers
    answers = []
    question_lines = [q.strip() for q in questions.split('\n') if q.strip().startswith('Q:')]

    print("\n💬 Please answer each question (or press Enter to skip):\n")

    for i, question in enumerate(question_lines, 1):
        # Remove "Q:" prefix
        clean_question = question[2:].strip()
        answer = input(f"{i}. {clean_question}\n   → ").strip()
        if answer:
            answers.append(f"Q: {clean_question}\nA: {answer}")

    # Combine user story with Q&A
    enhanced_context = f"""Original User Story:
{user_story}

Clarifying Questions and Answers:
{chr(10).join(answers) if answers else "No additional information provided"}"""

    return enhanced_context


def generate_detailed_issue(enhanced_story: str, repo_context: Dict[str, Any]) -> Dict[str, str]:
    """
    Use AI to generate a detailed GitHub issue

    Args:
        enhanced_story: User story with Q&A
        repo_context: Repository context

    Returns:
        Dict with 'title' and 'body'
    """
    system_prompt = """You are a Product Owner creating detailed GitHub issues for AI agents to implement.

Create a comprehensive issue with the following structure:

## Overview
Brief summary of the feature

## Requirements
Clear, specific requirements based on the user story and answers

## Constraints
Important limitations:
- What should NOT be changed
- What must be preserved
- Any technical constraints

## Implementation Guidelines
Specific technical guidance for the AI agent

## Testing Requirements
Test checklist items

## Acceptance Criteria
Checklist of what must be true when done

## Priority & Complexity
Assessment of urgency and difficulty

Be specific and actionable. The AI agent will read this and implement it."""

    prompt = f"""Create a detailed GitHub issue based on this information:

{enhanced_story}

Repository Context:
{repo_context}

Generate:
1. A concise title (format: "Feature: <description>" or "Fix: <description>")
2. A comprehensive issue body using the structure from the system prompt

Format your response as:
TITLE: <the title>

BODY:
<the body>"""

    print("\n🤖 Generating detailed issue with AI...")
    response = call_claude_api(prompt, system_prompt)

    # Parse response
    lines = response.split('\n')
    title = ""
    body_lines = []
    in_body = False

    for line in lines:
        if line.startswith("TITLE:"):
            title = line[6:].strip()
        elif line.startswith("BODY:"):
            in_body = True
        elif in_body:
            body_lines.append(line)

    body = '\n'.join(body_lines).strip()

    return {
        'title': title,
        'body': body
    }


def detect_repo_type(repo_path: Path) -> str:
    """Detect repository type/framework"""
    if (repo_path / "package.json").exists():
        return "JavaScript/Node.js"
    elif (repo_path / "requirements.txt").exists() or (repo_path / "setup.py").exists():
        return "Python"
    elif (repo_path / "go.mod").exists():
        return "Go"
    elif (repo_path / "Cargo.toml").exists():
        return "Rust"
    else:
        return "Unknown"


def create_issue_on_github(repo_path: Path, title: str, body: str, labels: list = None) -> Optional[str]:
    """
    Create GitHub issue using gh CLI

    Args:
        repo_path: Path to repository
        title: Issue title
        body: Issue body
        labels: List of labels to add

    Returns:
        Issue URL if successful
    """
    if labels is None:
        labels = ['enhancement', 'ready-for-dev']

    try:
        cmd = [
            'gh', 'issue', 'create',
            '--title', title,
            '--body', body,
            '--label', ','.join(labels)
        ]

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            issue_url = result.stdout.strip()
            return issue_url
        else:
            print(f"❌ Failed to create issue: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print("❌ Timeout creating issue")
        return None
    except Exception as e:
        print(f"❌ Error creating issue: {e}")
        return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Create detailed GitHub issue from user story using AI'
    )
    parser.add_argument(
        '--repo',
        required=True,
        help='Path to local repository'
    )
    parser.add_argument(
        '--story',
        help='User story text (if not provided, will prompt interactively)'
    )
    parser.add_argument(
        '--skip-questions',
        action='store_true',
        help='Skip clarifying questions and generate issue directly'
    )
    parser.add_argument(
        '--labels',
        help='Comma-separated labels (default: enhancement,ready-for-dev)',
        default='enhancement,ready-for-dev'
    )

    args = parser.parse_args()

    # Resolve repository path
    repo_path = Path(args.repo).expanduser().resolve()

    if not repo_path.exists():
        print(f"❌ Repository path does not exist: {repo_path}")
        return 1

    print("="*60)
    print("📝 GitHub Issue Creator with AI Enhancement")
    print("="*60)
    print(f"Repository: {repo_path}")
    print("="*60)

    # Check prerequisites
    gh_ok, gh_msg = check_gh_cli()
    if not gh_ok:
        print(f"\n❌ {gh_msg}")
        if "not installed" in gh_msg:
            print("   Install: brew install gh")
        else:
            print("   Authenticate: gh auth login")
        return 1

    # Setup repository if needed
    print("\n🔧 Checking repository setup...")

    # Initialize git if needed
    if not check_if_git_repo(repo_path):
        print("  → Initializing git repository...")
        if not init_git_repo(repo_path):
            return 1
    else:
        print("  ✓ Git repository exists")

    # Check for remote
    has_remote, remote_url = check_git_remote(repo_path)
    if not has_remote:
        print("\n⚠️  No GitHub remote found")
        create_repo = input("Create GitHub repository? (y/n): ").lower().strip() == 'y'

        if create_repo:
            repo_name = input(f"Repository name [{repo_path.name}]: ").strip() or repo_path.name
            description = input("Description: ").strip() or "AI-managed repository"

            success, repo_url = create_github_repo(
                repo_path,
                repo_name,
                description,
                public=True
            )

            if not success:
                return 1

            print(f"  ✓ Repository created: {repo_url}")
        else:
            print("❌ GitHub repository required to create issues")
            return 1
    else:
        print(f"  ✓ Remote exists: {remote_url}")

    # Enable issues and create labels
    print("  → Ensuring issues enabled and labels exist...")
    enable_issues(repo_path)
    create_labels(repo_path)

    # Get user story
    if args.story:
        user_story = args.story
    else:
        print("\n📖 Enter your user story:")
        print("   (You can enter multiple lines. Press Ctrl+D or Ctrl+Z when done)\n")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        user_story = '\n'.join(lines).strip()

    if not user_story:
        print("❌ No user story provided")
        return 1

    print(f"\n📝 User Story:\n{user_story}\n")

    # Detect repository type
    repo_type = detect_repo_type(repo_path)
    repo_context = {
        'path': str(repo_path),
        'name': repo_path.name,
        'type': repo_type
    }

    # Ask clarifying questions (unless skipped)
    if args.skip_questions:
        enhanced_story = user_story
    else:
        enhanced_story = ask_clarifying_questions(user_story, repo_context)

    # Generate detailed issue
    issue_data = generate_detailed_issue(enhanced_story, repo_context)

    # Show preview
    print("\n" + "="*60)
    print("📋 ISSUE PREVIEW")
    print("="*60)
    print(f"\nTitle: {issue_data['title']}\n")
    print("Body:")
    print(issue_data['body'])
    print("\n" + "="*60)

    # Confirm creation
    confirm = input("\n✅ Create this issue on GitHub? (y/n): ").lower().strip()

    if confirm != 'y':
        print("❌ Issue creation cancelled")
        return 0

    # Create issue
    labels = [l.strip() for l in args.labels.split(',')]
    issue_url = create_issue_on_github(
        repo_path,
        issue_data['title'],
        issue_data['body'],
        labels
    )

    if issue_url:
        print(f"\n✅ Issue created successfully!")
        print(f"   {issue_url}")
        print("\n📝 Next steps:")
        print(f"   python test_single_agent_github.py --repo {repo_path} --verbose")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
