#!/usr/bin/env python3
"""
Clarification Agent - Asks questions before starting work

This agent analyzes an issue and generates clarifying questions
that a developer would ask during a sprint planning meeting.
"""

import os
from typing import List, Dict, Any
import anthropic


class ClarificationAgent:
    """
    Agent that generates clarifying questions for issues
    """

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    def analyze_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze issue and generate clarifying questions

        Args:
            issue: Issue details (title, body, labels)

        Returns:
            Dictionary with:
            - needs_clarification: bool
            - questions: List[str]
            - reasoning: str
        """
        title = issue.get("title", "")
        body = issue.get("body", "")
        labels = issue.get("labels", [])

        prompt = f"""You are a senior developer reviewing a GitHub issue during sprint planning.

Issue Title: {title}

Issue Body:
{body}

Labels: {', '.join(labels)}

Your task:
1. Analyze if this issue has enough detail to implement
2. If unclear, generate 3-5 specific, actionable questions you would ask the product owner

Consider:
- Are requirements clear and unambiguous?
- Are acceptance criteria testable and complete?
- Are edge cases sufficiently covered?
- Is the technical approach feasible?
- Are there missing details about behavior, UI, or data?
- Are dependencies and integrations clear?

Format your response as JSON:
{{
  "needs_clarification": true/false,
  "questions": [
    "Specific question 1?",
    "Specific question 2?",
    ...
  ],
  "reasoning": "Brief explanation of what's unclear"
}}

If the issue is clear and complete, return needs_clarification: false with empty questions array.

Return ONLY the JSON, no other text."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        response_text = response.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)
        return result

    def post_questions_to_github(
        self,
        repository: str,
        issue_number: int,
        questions: List[str],
        reasoning: str
    ) -> None:
        """
        Post clarifying questions as GitHub issue comment

        Args:
            repository: Repository in format "owner/repo"
            issue_number: Issue number
            questions: List of questions
            reasoning: Why clarification is needed
        """
        import subprocess

        # Format comment
        comment = "## ❓ Clarification Needed\n\n"
        comment += f"{reasoning}\n\n"
        comment += "### Questions for Product Owner:\n\n"

        for i, question in enumerate(questions, 1):
            comment += f"{i}. {question}\n"

        comment += "\n---\n"
        comment += "**Please answer these questions so development can proceed.**\n"
        comment += "Once answered, remove the `needs-clarification` label and re-add `ai-ready`.\n"

        # Post comment using gh CLI
        subprocess.run(
            [
                "gh", "issue", "comment", str(issue_number),
                "--repo", repository,
                "--body", comment
            ],
            check=True,
            capture_output=True,
            timeout=30
        )

    def add_clarification_label(
        self,
        repository: str,
        issue_number: int
    ) -> None:
        """
        Add needs-clarification label and remove ai-ready

        Args:
            repository: Repository in format "owner/repo"
            issue_number: Issue number
        """
        import subprocess

        # Add needs-clarification label, remove ai-ready
        subprocess.run(
            [
                "gh", "issue", "edit", str(issue_number),
                "--repo", repository,
                "--add-label", "needs-clarification",
                "--remove-label", "ai-ready"
            ],
            check=True,
            capture_output=True,
            timeout=30
        )


def check_issue_for_clarification(
    repository: str,
    issue_number: int,
    title: str,
    body: str,
    labels: List[str]
) -> bool:
    """
    Check if issue needs clarification and post questions if needed

    Args:
        repository: Repository in format "owner/repo"
        issue_number: Issue number
        title: Issue title
        body: Issue body
        labels: Issue labels

    Returns:
        True if clarification needed, False otherwise
    """
    agent = ClarificationAgent()

    # Analyze issue
    result = agent.analyze_issue({
        "title": title,
        "body": body,
        "labels": labels
    })

    if result["needs_clarification"]:
        print(f"❓ Issue #{issue_number} needs clarification")
        print(f"   Reason: {result['reasoning']}")
        print(f"   Questions: {len(result['questions'])}")

        # Post questions to GitHub
        agent.post_questions_to_github(
            repository,
            issue_number,
            result["questions"],
            result["reasoning"]
        )

        # Update labels
        agent.add_clarification_label(repository, issue_number)

        return True
    else:
        print(f"✅ Issue #{issue_number} is clear - proceeding with work")
        return False
