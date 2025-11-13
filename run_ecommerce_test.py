#!/usr/bin/env python3
"""
Test script to run E-Commerce Dashboard build in external workspace
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
from orchestrator import Orchestrator

# Load environment
load_dotenv()

# Define external workspace
EXTERNAL_WORKSPACE = Path.home() / "Development/repos/ecommerce-dashboard"

# E-Commerce Dashboard User Story
USER_STORY = """Build a full-stack e-commerce dashboard with the following requirements:

## Customer Features:
1. Product catalog with search and filtering
2. Shopping cart functionality
3. Checkout process with order summary
4. User authentication (login/register)
5. Order history for logged-in users

## Admin Features:
1. Dashboard with sales analytics
2. Product management (CRUD operations)
3. Order management and status updates
4. Customer list view

## Technical Requirements:
- Frontend: React with TypeScript, Tailwind CSS
- Backend: Node.js with Express
- Database: SQLite for simplicity
- API: RESTful endpoints for all operations
- Authentication: JWT-based auth system

## Security Requirements:
- Input validation and sanitization on all forms
- SQL injection prevention (parameterized queries)
- CSRF protection
- XSS prevention
- Secure password hashing (bcrypt)

## Testing Requirements:
- Unit tests for critical business logic
- API endpoint tests
- At least 70% code coverage

## Deliverables:
- Complete source code with proper project structure
- README with setup instructions
- Database schema and migrations
- Test suite

Build this as a production-ready application with clean, maintainable code.
"""


def main():
    """Run the e-commerce dashboard workflow"""
    print(f"🚀 Starting E-Commerce Dashboard Build")
    print(f"📁 External Workspace: {EXTERNAL_WORKSPACE}")
    print("="*60)

    # Initialize orchestrator with external workspace
    try:
        orchestrator = Orchestrator(workspace_dir=EXTERNAL_WORKSPACE)
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        sys.exit(1)

    # Execute the workflow
    try:
        result = orchestrator.process_user_story(USER_STORY)

        # Print summary
        print("\n" + "="*60)
        print("📈 WORKFLOW SUMMARY")
        print("="*60)
        print(f"Status: {'✅ APPROVED' if result.approved else '❌ NOT APPROVED'}")
        print(f"Revisions: {result.revision_count}")
        print(f"Total Cost: ${result.total_cost:.4f}")

        if result.errors:
            print(f"\nErrors:")
            for error in result.errors:
                print(f"  - {error}")

        if result.po_decision:
            print(f"\nProduct Owner Decision:")
            print(f"  {result.po_decision[:300]}...")

        print("="*60)

        if result.approved:
            print("\n🎉 E-Commerce Dashboard completed successfully!")
            print(f"📂 Code available at: {EXTERNAL_WORKSPACE}")
        else:
            print("\n⚠️  Workflow did not complete successfully")

    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
