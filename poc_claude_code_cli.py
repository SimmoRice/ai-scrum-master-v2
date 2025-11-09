#!/usr/bin/env python3
"""
Proof of Concept: Claude Code CLI Integration

Tests that we can:
1. Call Claude Code from Python via CLI
2. Pass it a task
3. Get structured JSON output
4. Verify files were created
5. Check git commits

This proves the v2.0 architecture is viable.
"""
import subprocess
import json
from pathlib import Path
import shutil
import sys


def cleanup_workspace(workspace: Path):
    """Remove workspace if it exists"""
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)


def initialize_git(workspace: Path):
    """Initialize git repo in workspace"""
    subprocess.run(
        ["git", "init"],
        cwd=workspace,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "AI Scrum Master"],
        cwd=workspace,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "ai@scrum-master.local"],
        cwd=workspace,
        capture_output=True,
        check=True
    )


def run_claude_code_task(workspace: Path, task: str, system_prompt: str) -> dict:
    """
    Run Claude Code with a task

    Args:
        workspace: Working directory
        task: Task description
        system_prompt: System prompt for Claude

    Returns:
        {
            'success': bool,
            'output': str,
            'raw_stdout': str,
            'raw_stderr': str,
            'exit_code': int
        }
    """
    print(f"\n{'='*60}")
    print("🚀 Starting Claude Code...")
    print(f"{'='*60}")
    print(f"Workspace: {workspace}")
    print(f"Task: {task[:100]}...")
    print(f"{'='*60}\n")

    cmd = [
        "claude",
        "-p", task,
        "--output-format", "json",
        "--system-prompt", system_prompt,
        "--allowedTools", "Write,Read,Edit,Bash,Glob,Grep"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(workspace),  # Use cwd parameter of subprocess, not --cwd flag
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        print(f"Exit code: {result.returncode}")

        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                return {
                    'success': True,
                    'output': response,
                    'raw_stdout': result.stdout,
                    'raw_stderr': result.stderr,
                    'exit_code': result.returncode
                }
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse JSON: {e}")
                return {
                    'success': False,
                    'output': result.stdout,
                    'raw_stdout': result.stdout,
                    'raw_stderr': result.stderr,
                    'exit_code': result.returncode
                }
        else:
            return {
                'success': False,
                'output': None,
                'raw_stdout': result.stdout,
                'raw_stderr': result.stderr,
                'exit_code': result.returncode
            }

    except subprocess.TimeoutExpired:
        print("❌ Command timed out after 5 minutes")
        return {
            'success': False,
            'output': None,
            'raw_stdout': '',
            'raw_stderr': 'Timeout',
            'exit_code': -1
        }
    except FileNotFoundError:
        print("❌ 'claude' command not found. Is Claude Code installed?")
        return {
            'success': False,
            'output': None,
            'raw_stdout': '',
            'raw_stderr': 'claude command not found',
            'exit_code': -1
        }


def verify_files_created(workspace: Path, expected_files: list) -> dict:
    """Check if expected files were created"""
    print(f"\n{'='*60}")
    print("📁 Verifying files...")
    print(f"{'='*60}")

    results = {}
    for filename in expected_files:
        filepath = workspace / filename
        exists = filepath.exists()
        results[filename] = exists

        if exists:
            size = filepath.stat().st_size
            print(f"  ✅ {filename} ({size} bytes)")
        else:
            print(f"  ❌ {filename} NOT FOUND")

    return results


def verify_git_commits(workspace: Path) -> dict:
    """Check git commit history"""
    print(f"\n{'='*60}")
    print("🔍 Checking git commits...")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=True
        )

        commits = result.stdout.strip().split('\n') if result.stdout.strip() else []

        print(f"  Commits found: {len(commits)}")
        for commit in commits:
            print(f"    - {commit}")

        return {
            'has_commits': len(commits) > 0,
            'commit_count': len(commits),
            'commits': commits
        }
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Git log failed: {e}")
        return {
            'has_commits': False,
            'commit_count': 0,
            'commits': []
        }


def test_1_simple_file_creation():
    """Test 1: Can Claude Code create a simple file?"""
    print("\n" + "="*60)
    print("TEST 1: Simple File Creation")
    print("="*60)

    workspace = Path("./poc-workspace-test1")
    cleanup_workspace(workspace)

    system_prompt = """You are a helpful coding assistant.
Create files exactly as requested.
Keep it simple and focused."""

    task = """Create a file called hello.txt in the current working directory with the content:
Hello from Claude Code!
This is a proof of concept.

Do NOT create any other files. Make sure to create the file in the current working directory."""

    result = run_claude_code_task(workspace, task, system_prompt)

    print("\n📊 Result:")
    print(f"  Success: {result['success']}")
    if result['output']:
        print(f"  Output type: {type(result['output'])}")
        if isinstance(result['output'], dict):
            print(f"  Keys: {result['output'].keys()}")

    # Verify file
    file_results = verify_files_created(workspace, ['hello.txt'])

    # Summary
    test_passed = result['success'] and file_results.get('hello.txt', False)
    print(f"\n{'✅ TEST 1 PASSED' if test_passed else '❌ TEST 1 FAILED'}")

    return test_passed


def test_2_html_file_with_git():
    """Test 2: Can Claude Code create an HTML file and commit it?"""
    print("\n" + "="*60)
    print("TEST 2: HTML File + Git Commit")
    print("="*60)

    workspace = Path("./poc-workspace-test2")
    cleanup_workspace(workspace)
    initialize_git(workspace)

    system_prompt = """You are an Architect AI in a development team.
Create working code and commit it to git when complete.
Use best practices for HTML structure."""

    task = """Create a simple HTML page called index.html in the current working directory with:
1. Proper DOCTYPE and HTML structure
2. Title: "Proof of Concept"
3. Body with an h1: "Claude Code Works!"
4. A paragraph explaining this is a test
5. Some basic inline CSS to make it look nice

Then commit your work to git with a clear message.

IMPORTANT:
- Create the file in the current working directory (not /tmp or anywhere else)
- Actually create the file and commit it, don't just describe what to do"""

    result = run_claude_code_task(workspace, task, system_prompt)

    print("\n📊 Result:")
    print(f"  Success: {result['success']}")

    # Verify files
    file_results = verify_files_created(workspace, ['index.html'])

    # Verify git commits
    git_results = verify_git_commits(workspace)

    # Summary
    test_passed = (
        result['success'] and
        file_results.get('index.html', False) and
        git_results['has_commits']
    )
    print(f"\n{'✅ TEST 2 PASSED' if test_passed else '❌ TEST 2 FAILED'}")

    return test_passed


def test_3_multi_file_project():
    """Test 3: Can Claude Code create multiple files and structure them?"""
    print("\n" + "="*60)
    print("TEST 3: Multi-File Project")
    print("="*60)

    workspace = Path("./poc-workspace-test3")
    cleanup_workspace(workspace)
    initialize_git(workspace)

    system_prompt = """You are an Architect AI.
Create well-structured projects with multiple files.
Commit your work when complete."""

    task = """Create a simple calculator web app in the current working directory with:

FILES (create in current directory):
1. index.html - HTML structure with calculator UI
2. calculator.js - JavaScript calculator logic
3. styles.css - CSS styling

REQUIREMENTS:
- Clean, working code
- All files should reference each other correctly
- Add basic functionality (add, subtract, multiply, divide)
- Commit all files to git when done

IMPORTANT:
- Create ALL three files in the current working directory
- Do NOT create files in /tmp or any other location
- Commit them to git when complete"""

    result = run_claude_code_task(workspace, task, system_prompt)

    print("\n📊 Result:")
    print(f"  Success: {result['success']}")

    # Verify files
    expected_files = ['index.html', 'calculator.js', 'styles.css']
    file_results = verify_files_created(workspace, expected_files)

    # Verify git commits
    git_results = verify_git_commits(workspace)

    # Summary
    all_files_created = all(file_results.values())
    test_passed = (
        result['success'] and
        all_files_created and
        git_results['has_commits']
    )
    print(f"\n{'✅ TEST 3 PASSED' if test_passed else '❌ TEST 3 FAILED'}")

    return test_passed


def main():
    """Run all proof-of-concept tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          CLAUDE CODE CLI - PROOF OF CONCEPT               ║
║                                                           ║
║  Testing if we can control Claude Code programmatically  ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Check if claude command exists
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Claude Code found: {result.stdout.strip()}\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Claude Code not found or not working")
        print("\nPlease ensure Claude Code is installed and the 'claude' command is in your PATH")
        print("Installation: https://claude.com/code")
        sys.exit(1)

    # Run tests
    results = {}

    try:
        results['test_1'] = test_1_simple_file_creation()
    except Exception as e:
        print(f"\n❌ Test 1 crashed: {e}")
        results['test_1'] = False

    try:
        results['test_2'] = test_2_html_file_with_git()
    except Exception as e:
        print(f"\n❌ Test 2 crashed: {e}")
        results['test_2'] = False

    try:
        results['test_3'] = test_3_multi_file_project()
    except Exception as e:
        print(f"\n❌ Test 3 crashed: {e}")
        results['test_3'] = False

    # Final summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_status in results.items():
        status = "✅ PASS" if passed_status else "❌ FAIL"
        print(f"  {test_name}: {status}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Proof of Concept SUCCESSFUL!")
        print("✅ v2.0 architecture is VIABLE using Claude Code CLI")
        print("\nNext steps:")
        print("  1. Design the full orchestrator architecture")
        print("  2. Implement ClaudeCodeAgent class")
        print("  3. Build the sequential workflow")
        print("  4. Add Product Owner review logic")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        print("\nThis may indicate:")
        print("  - Claude Code CLI behaves differently than expected")
        print("  - Need to adjust command flags")
        print("  - JSON output format needs investigation")
        print("\nCheck the output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
