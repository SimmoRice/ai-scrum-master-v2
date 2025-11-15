# Test Project: Task Management Web App

This project specification is designed to test the queue blocking system by creating a complex app with ~15-20 tasks, dependencies, and multiple iterations.

## Project Overview

Build a full-stack task management web application with user authentication, real-time updates, and advanced filtering.

## Core Requirements

### Phase 1: Foundation & Backend (5-6 tasks)
**These should be done first and have dependencies**

1. **Project Structure & Database Setup**
   - Initialize Node.js/Express backend
   - Setup SQLite database with migrations
   - Create basic folder structure (routes, models, middleware, public)
   - Add environment variable support (.env)
   - Setup package.json with all dependencies

2. **User Authentication System**
   - User registration endpoint (POST /api/auth/register)
   - Login endpoint with JWT tokens (POST /api/auth/login)
   - Password hashing with bcrypt
   - JWT middleware for protected routes
   - Logout functionality

3. **Task Database Schema & Models**
   - Tasks table (id, title, description, status, priority, due_date, user_id, created_at, updated_at)
   - Database model with CRUD operations
   - Foreign key relationship to users table
   - Status enum: 'pending', 'in-progress', 'completed'
   - Priority enum: 'low', 'medium', 'high'

4. **Task API Endpoints**
   - GET /api/tasks - List all tasks for logged-in user
   - POST /api/tasks - Create new task
   - GET /api/tasks/:id - Get single task
   - PUT /api/tasks/:id - Update task
   - DELETE /api/tasks/:id - Delete task
   - All endpoints require authentication

5. **Input Validation & Error Handling**
   - Validate all incoming requests (title required, status valid, etc.)
   - Centralized error handling middleware
   - Return appropriate HTTP status codes
   - Consistent error response format
   - Sanitize user inputs to prevent SQL injection

### Phase 2: Frontend Core (4-5 tasks)
**Depends on Phase 1 tasks**

6. **HTML Structure & Base CSS**
   - Create index.html with semantic HTML
   - Login/Register forms
   - Task list container
   - Task creation form
   - Mobile-responsive layout with CSS Grid/Flexbox
   - CSS variables for theming

7. **Authentication UI & Logic**
   - Login form with email/password
   - Registration form with validation
   - Store JWT token in localStorage
   - Auto-redirect when not authenticated
   - Logout button functionality
   - Show current user's email

8. **Task Display & List Management**
   - Fetch and display all tasks from API
   - Display task cards with all fields
   - Show task status with colored badges
   - Show priority with icons
   - Format due dates nicely
   - Empty state when no tasks

9. **Task Creation & Editing**
   - Form to create new task (title, description, priority, due date)
   - Edit existing task (inline or modal)
   - Delete task with confirmation
   - Form validation on client side
   - Success/error notifications
   - Clear form after submission

### Phase 3: Advanced Features (5-6 tasks)
**Some independent, some depend on Phase 2**

10. **Task Filtering & Search** (Independent)
    - Filter by status dropdown
    - Filter by priority dropdown
    - Search by title/description
    - Combine multiple filters
    - Show count of filtered tasks
    - Clear all filters button

11. **Task Sorting** (Independent)
    - Sort by due date (ascending/descending)
    - Sort by priority
    - Sort by created date
    - Sort by status
    - Remember sort preference in localStorage

12. **Dark Mode Toggle** (Independent)
    - Toggle button in header
    - CSS variables for dark theme
    - Smooth transition between themes
    - Remember preference in localStorage
    - Different colors for task status badges in dark mode

13. **Task Statistics Dashboard**
    - Display total tasks count
    - Count by status (pending/in-progress/completed)
    - Count by priority
    - Percentage completed
    - Overdue tasks count
    - Visual charts (can be simple CSS bars)

14. **Due Date Notifications**
    - Highlight overdue tasks in red
    - Show "due today" badge
    - Show "due this week" badge
    - Sort overdue tasks to top
    - Visual indicator for urgency

15. **Drag and Drop Status Update** (Depends on task display)
    - Drag tasks between status columns
    - Update status via API on drop
    - Smooth animations
    - Visual feedback during drag
    - Revert on API error

### Phase 4: Polish & Testing (3-4 tasks)

16. **Form Validation Improvements**
    - Real-time validation feedback
    - Highlight invalid fields
    - Show specific error messages
    - Prevent duplicate submissions
    - Disable submit button while loading

17. **Loading States & UX**
    - Loading spinner while fetching tasks
    - Loading state for buttons during API calls
    - Skeleton screens for task cards
    - Optimistic UI updates
    - Retry failed requests

18. **Responsive Design Refinement**
    - Test on mobile (320px+)
    - Test on tablet (768px+)
    - Test on desktop (1024px+)
    - Adjust layouts for each breakpoint
    - Touch-friendly button sizes on mobile

19. **Error Handling & Edge Cases**
    - Handle network errors gracefully
    - Handle expired JWT tokens
    - Handle server errors (500)
    - Handle validation errors
    - Handle duplicate requests
    - Add error boundaries

20. **Documentation & README**
    - Installation instructions
    - API documentation
    - Environment variables setup
    - How to run locally
    - Screenshots
    - Technology stack explanation

## Technical Stack

- **Backend**: Node.js + Express.js
- **Database**: SQLite with better-sqlite3
- **Auth**: JWT (jsonwebtoken), bcrypt
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **Validation**: express-validator
- **No build tools** - just static files served by Express

## Expected Dependencies

These dependencies will trigger the queue blocking behavior:

```
Task 1: Project Setup
  └─> Task 2: Auth (needs DB)
      └─> Task 4: Task API (needs auth middleware)
          └─> Task 7: Auth UI (needs auth endpoints)
              └─> Task 8: Task Display (needs task API)
                  └─> Task 9: Task Creation (needs task display)
                      └─> Task 15: Drag & Drop (needs task display)

Task 3: Database Schema
  └─> Task 4: Task API (needs schema)

Task 6: HTML/CSS (Independent - can run in parallel)
Task 10: Filtering (Independent once API exists)
Task 11: Sorting (Independent once API exists)
Task 12: Dark Mode (Independent)
Task 13: Statistics (Depends on task data)
Task 14: Due Date (Independent once API exists)
```

## How This Tests Queue Blocking

1. **Initial Rush**:
   - Workers pick up tasks 1-6 simultaneously
   - Queue hits 5 PR limit quickly
   - Testing MAX_PENDING_PRS blocking

2. **Dependency Blocking**:
   - Task 7 can't proceed until Task 2 is merged
   - Task 15 can't proceed until Task 8 is merged
   - Tests dependency tracking

3. **Parallel Independent Work**:
   - Tasks 10, 11, 12, 14 are independent
   - Should be able to proceed while others are blocked
   - Tests ALLOW_PARALLEL_INDEPENDENT

4. **Changes Requested Scenario**:
   - Request changes on Task 2 (auth)
   - Everything should BLOCK immediately
   - Tests BLOCK_ON_CHANGES_REQUESTED

5. **Iterative Reviews**:
   - Approve/merge tasks 1-5 in batches
   - Watch queue unblock and workers resume
   - Tests the full review workflow

## Testing Strategy

### Step 1: Create Test Repository
```bash
gh repo create YOUR_USERNAME/taskmaster-app --public --clone
cd taskmaster-app
echo "# TaskMaster - AI-Built Task Manager" > README.md
git add README.md && git commit -m "Initial commit" && git push
```

### Step 2: Setup Labels
```bash
cd ~/Development/repos/ai-scrum-master-v2
python setup_repo_labels.py --repo YOUR_USERNAME/taskmaster-app
```

### Step 3: Configure Cluster (Conservative Settings)
```bash
# On Proxmox
ssh root@proxmox-host
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    echo 'MAX_PENDING_PRS=3' >> .env
    echo 'BLOCK_ON_CHANGES_REQUESTED=true' >> .env
    echo 'ALLOW_PARALLEL_INDEPENDENT=true' >> .env
"
pct exec 200 -- systemctl restart ai-orchestrator
```

### Step 4: Add Repo to Cluster
```bash
cd /root/ai-scrum-master-v2/deployment/proxmox
./configure_multi_repo.sh "SimmoRice/ai-scrum-master-v2,YOUR_USERNAME/taskmaster-app"
```

### Step 5: Generate Issues
```bash
cd ~/Development/repos/ai-scrum-master-v2
python create_project_issues.py \
  --repo YOUR_USERNAME/taskmaster-app \
  --project-file test_queue_blocking_project.md
```

### Step 6: Watch the Magic Happen

**Monitor queue blocking:**
```bash
# Terminal 1: Watch queue status
watch -n 5 'curl -s http://192.168.100.200:8000/health | jq ".pr_review"'

# Terminal 2: Watch worker activity
watch -n 5 'curl -s http://192.168.100.200:8000/workers | jq'

# Terminal 3: Watch orchestrator logs
ssh root@proxmox
cd /root/ai-scrum-master-v2/deployment/proxmox
./view_logs.sh orchestrator | grep -i "blocked\|pending\|approved"
```

### Step 7: Test Blocking Scenarios

**Scenario A: Threshold Blocking**
```bash
# Workers create 3 PRs (your threshold)
# Queue should block
curl http://192.168.100.200:8000/health | jq '.pr_review.queue_blocked'
# Should be: true

# Approve 2 PRs
python review_prs.py --repo YOUR_USERNAME/taskmaster-app --approve 1,2 --merge

# Queue should unblock
curl http://192.168.100.200:8000/health | jq '.pr_review.queue_blocked'
# Should be: false
```

**Scenario B: Changes Requested Blocking**
```bash
# Request changes on any PR
python review_prs.py --repo YOUR_USERNAME/taskmaster-app \
  --request-changes 3 \
  --comment "Please add error handling for invalid JWT tokens"

# Queue should IMMEDIATELY block
curl http://192.168.100.200:8000/health | jq '.pr_review'
# blocking_reason should mention changes requested

# All workers should pause
curl http://192.168.100.200:8000/workers | jq
# All should show no current_task
```

**Scenario C: Parallel Independent Work**
```bash
# After some foundation PRs are merged
# Independent tasks (10, 11, 12) should still be available

# Check pending work
curl http://192.168.100.200:8000/queue | jq '.pending'

# Should see independent tasks available even with some PRs pending
```

## Expected Timeline

- **0-5 min**: Workers pick up first 3 tasks, queue blocks
- **5-10 min**: You review and approve first batch, queue unblocks
- **10-15 min**: Workers pick up next 3, queue blocks again
- **15-20 min**: You request changes on one PR, everything blocks
- **20-25 min**: PR updated, you approve, queue unblocks
- **25-45 min**: Iterative review cycles
- **45-60 min**: Final tasks complete, all PRs merged

## Success Criteria

✅ Queue blocks at 3 pending PRs
✅ Queue immediately blocks when changes requested
✅ Independent tasks proceed while dependent ones blocked
✅ Workers pause when queue blocked
✅ Workers resume when queue unblocks
✅ All PRs get reviewed before merge
✅ Final app is functional
✅ No cascading bugs from unreviewed code

## Alternative: Simpler Calculator Test

If the task manager is too complex, try this simpler version:

**Advanced Calculator (10 tasks)**
1. Project setup & HTML structure
2. Basic arithmetic (+, -, ×, ÷)
3. Decimal point support
4. Clear and backspace
5. Keyboard support
6. Calculation history (last 10)
7. Memory functions (M+, M-, MR, MC)
8. Scientific functions (√, x², sin, cos, tan)
9. Dark mode toggle
10. Responsive design & polish

This will create 10 issues, perfect for testing with MAX_PENDING_PRS=3-5.
