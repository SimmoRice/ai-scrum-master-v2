#!/usr/bin/env python3
"""
Parallel Agent Test Suite

Comprehensive tests for parallel AI Scrum Master operations including:
- Multi-worker deployment
- Concurrent execution
- Load balancing
- Conflict prevention
- Resource isolation
- Performance benchmarking

Usage:
    # Run all tests
    python test_parallel_agents.py

    # Run specific test
    python test_parallel_agents.py --test test_concurrent_execution

    # Run with specific worker count
    python test_parallel_agents.py --workers 5

    # Run performance benchmark
    python test_parallel_agents.py --benchmark
"""

import os
import sys
import time
import unittest
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import multiprocessing

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import Orchestrator, WorkflowResult
from deploy_parallel_agents import ParallelAgentManager


# Global functions for multiprocessing (can't use local functions)
def _simulate_task(args):
    """Simulate a simple task"""
    task_id, workspace = args
    workspace.mkdir(parents=True, exist_ok=True)
    time.sleep(1)  # Simulate work
    return {
        "task_id": task_id,
        "success": True,
        "duration": 1.0,
        "cost": 0.05
    }


def _increment_counter(args):
    """Simulate worker incrementing shared counter"""
    worker_id, num_increments, shared_file = args
    import fcntl

    for _ in range(num_increments):
        # Use file locking to prevent race conditions
        with open(shared_file, "r+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                value = int(f.read() or "0")
                value += 1
                f.seek(0)
                f.truncate()
                f.write(str(value))
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        time.sleep(0.01)  # Simulate work

    return worker_id


def _task_with_failure(args):
    """Task that may fail"""
    task_id, should_fail = args
    if should_fail:
        raise Exception(f"Task {task_id} intentionally failed")

    time.sleep(0.5)
    return {"task_id": task_id, "success": True}


def _task_with_tracking(task_id):
    """Task that tracks which worker processed it"""
    worker_id = multiprocessing.current_process().name
    time.sleep(0.5)
    return {"task_id": task_id, "worker_id": worker_id}


def _benchmark_task(task_id):
    """Simulated task with fixed duration"""
    time.sleep(0.5)  # Simulate 0.5s of work
    return {"task_id": task_id, "duration": 0.5}


@dataclass
class TestResult:
    """Result from a single test execution"""
    test_name: str
    success: bool
    duration: float
    error: str = None
    metrics: Dict[str, Any] = None


class ParallelAgentTestSuite(unittest.TestCase):
    """Test suite for parallel agent operations"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_workspace = Path(tempfile.mkdtemp(prefix="parallel_test_"))
        cls.num_workers = 3
        print(f"\n🧪 Test workspace: {cls.test_workspace}")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if cls.test_workspace.exists():
            shutil.rmtree(cls.test_workspace)
        print(f"\n✅ Cleaned up test workspace")

    def test_worker_deployment(self):
        """Test that workers can be deployed successfully"""
        print("\n" + "="*80)
        print("TEST: Worker Deployment")
        print("="*80)

        manager = ParallelAgentManager(
            num_workers=self.num_workers,
            mode="test",
            workspace_base=self.test_workspace / "deployment"
        )

        try:
            manager.deploy_workers()

            # Verify all workers are created
            self.assertEqual(len(manager.workers), self.num_workers)

            # Verify worker states
            for worker_id, worker in manager.workers.items():
                self.assertIsNotNone(worker.worker_id)
                self.assertEqual(worker.status, "idle")
                print(f"  ✅ {worker_id} deployed")

            print(f"\n✅ Successfully deployed {self.num_workers} workers")

        finally:
            manager.shutdown()

    def test_workspace_isolation(self):
        """Test that workers have isolated workspaces"""
        print("\n" + "="*80)
        print("TEST: Workspace Isolation")
        print("="*80)

        workspace_base = self.test_workspace / "isolation"
        manager = ParallelAgentManager(
            num_workers=self.num_workers,
            mode="test",
            workspace_base=workspace_base
        )

        try:
            manager.deploy_workers()

            # Verify each worker has its own workspace
            for worker_id in manager.workers.keys():
                worker_workspace = workspace_base / worker_id
                self.assertTrue(worker_workspace.exists())
                print(f"  ✅ {worker_id} has isolated workspace: {worker_workspace}")

            # Create test files in each workspace
            for worker_id in manager.workers.keys():
                worker_workspace = workspace_base / worker_id
                test_file = worker_workspace / "test.txt"
                test_file.write_text(f"Worker: {worker_id}")

            # Verify files are isolated
            for worker_id in manager.workers.keys():
                worker_workspace = workspace_base / worker_id
                test_file = worker_workspace / "test.txt"
                content = test_file.read_text()
                self.assertEqual(content, f"Worker: {worker_id}")
                print(f"  ✅ {worker_id} workspace isolated")

            print(f"\n✅ All {self.num_workers} workspaces properly isolated")

        finally:
            manager.shutdown()

    def test_concurrent_execution(self):
        """Test concurrent execution of multiple simple tasks"""
        print("\n" + "="*80)
        print("TEST: Concurrent Execution")
        print("="*80)

        num_tasks = 6
        num_workers = 3
        workspace_base = self.test_workspace / "concurrent"

        # Execute tasks in parallel
        start_time = time.time()

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(
                    _simulate_task,
                    (task_id, workspace_base / f"task-{task_id}")
                ): task_id
                for task_id in range(num_tasks)
            }

            results = []
            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"  ✅ Task {task_id} completed")
                except Exception as e:
                    print(f"  ❌ Task {task_id} failed: {e}")
                    results.append({"task_id": task_id, "success": False})

        duration = time.time() - start_time

        # Verify results
        self.assertEqual(len(results), num_tasks)
        successful = sum(1 for r in results if r.get("success"))
        self.assertEqual(successful, num_tasks)

        # Check parallelization benefit
        sequential_time = num_tasks * 1.0
        speedup = sequential_time / duration

        print(f"\n📊 Execution Statistics:")
        print(f"  Tasks: {num_tasks}")
        print(f"  Workers: {num_workers}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Sequential time: {sequential_time:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"\n✅ Concurrent execution working (speedup: {speedup:.2f}x)")

        # Expect at least 1.5x speedup with 3 workers
        self.assertGreater(speedup, 1.5)

    def test_resource_contention(self):
        """Test handling of resource contention between workers"""
        print("\n" + "="*80)
        print("TEST: Resource Contention")
        print("="*80)

        # Simulate multiple workers trying to access shared resource
        shared_file = self.test_workspace / "shared_resource.txt"
        shared_file.write_text("0")

        num_workers = 3
        increments_per_worker = 10
        expected_total = num_workers * increments_per_worker

        # Execute in parallel
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(_increment_counter, (worker_id, increments_per_worker, shared_file))
                for worker_id in range(num_workers)
            ]

            for future in as_completed(futures):
                worker_id = future.result()
                print(f"  ✅ Worker {worker_id} completed")

        # Verify final value
        final_value = int(shared_file.read_text())

        print(f"\n📊 Contention Test Results:")
        print(f"  Workers: {num_workers}")
        print(f"  Increments/worker: {increments_per_worker}")
        print(f"  Expected total: {expected_total}")
        print(f"  Actual total: {final_value}")

        self.assertEqual(final_value, expected_total)
        print(f"\n✅ Resource contention handled correctly")

    def test_failure_isolation(self):
        """Test that worker failures don't affect other workers"""
        print("\n" + "="*80)
        print("TEST: Failure Isolation")
        print("="*80)

        num_tasks = 6
        failing_tasks = {1, 3}  # Tasks 1 and 3 will fail

        with ProcessPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(_task_with_failure, (task_id, task_id in failing_tasks)): task_id
                for task_id in range(num_tasks)
            }

            results = []
            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    result = future.result()
                    results.append({"task_id": task_id, "success": True})
                    print(f"  ✅ Task {task_id} succeeded")
                except Exception as e:
                    results.append({"task_id": task_id, "success": False, "error": str(e)})
                    print(f"  ❌ Task {task_id} failed (expected)")

        # Verify only expected tasks failed
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        self.assertEqual(len(failed), len(failing_tasks))
        self.assertEqual(len(successful), num_tasks - len(failing_tasks))

        print(f"\n📊 Failure Isolation Results:")
        print(f"  Total tasks: {num_tasks}")
        print(f"  Expected failures: {len(failing_tasks)}")
        print(f"  Actual failures: {len(failed)}")
        print(f"  Successful: {len(successful)}")
        print(f"\n✅ Failures properly isolated")

    def test_load_balancing(self):
        """Test load distribution across workers"""
        print("\n" + "="*80)
        print("TEST: Load Balancing")
        print("="*80)

        num_tasks = 12
        num_workers = 3

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(_task_with_tracking, task_id) for task_id in range(num_tasks)]

            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                print(f"  ✅ Task {result['task_id']} processed by {result['worker_id']}")

        # Analyze distribution
        worker_counts = {}
        for result in results:
            worker_id = result["worker_id"]
            worker_counts[worker_id] = worker_counts.get(worker_id, 0) + 1

        print(f"\n📊 Load Distribution:")
        for worker_id, count in sorted(worker_counts.items()):
            percentage = (count / num_tasks) * 100
            print(f"  {worker_id}: {count} tasks ({percentage:.1f}%)")

        # Verify reasonably balanced (no worker should have < 20% or > 50% of tasks)
        expected_per_worker = num_tasks / num_workers
        for worker_id, count in worker_counts.items():
            deviation = abs(count - expected_per_worker) / expected_per_worker
            self.assertLess(deviation, 0.5)  # Within 50% of expected

        print(f"\n✅ Load reasonably balanced across workers")

    def test_performance_benchmark(self):
        """Benchmark parallel vs sequential execution"""
        print("\n" + "="*80)
        print("TEST: Performance Benchmark")
        print("="*80)

        num_tasks = 6

        # Sequential execution
        print("\n📊 Sequential execution...")
        start_time = time.time()
        seq_results = []
        for task_id in range(num_tasks):
            result = _benchmark_task(task_id)
            seq_results.append(result)
            print(f"  Task {task_id} completed")
        seq_duration = time.time() - start_time

        # Parallel execution (3 workers)
        print("\n📊 Parallel execution (3 workers)...")
        start_time = time.time()
        with ProcessPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(_benchmark_task, task_id) for task_id in range(num_tasks)]
            par_results = [future.result() for future in as_completed(futures)]
            for result in par_results:
                print(f"  Task {result['task_id']} completed")
        par_duration = time.time() - start_time

        speedup = seq_duration / par_duration
        efficiency = speedup / 3  # 3 workers

        print(f"\n📊 Benchmark Results:")
        print(f"  Tasks: {num_tasks}")
        print(f"  Sequential time: {seq_duration:.2f}s")
        print(f"  Parallel time: {par_duration:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Efficiency: {efficiency*100:.1f}%")

        # Expect at least 2x speedup with 3 workers on 6 tasks
        self.assertGreater(speedup, 2.0)
        print(f"\n✅ Performance benchmark passed (speedup: {speedup:.2f}x)")


class ParallelIntegrationTests(unittest.TestCase):
    """Integration tests for full parallel workflows"""

    def test_manager_lifecycle(self):
        """Test full manager lifecycle: deploy, monitor, shutdown"""
        print("\n" + "="*80)
        print("INTEGRATION TEST: Manager Lifecycle")
        print("="*80)

        workspace = Path(tempfile.mkdtemp(prefix="lifecycle_test_"))

        try:
            manager = ParallelAgentManager(
                num_workers=2,
                mode="test",
                workspace_base=workspace
            )

            # Deploy
            print("\n📦 Deploying workers...")
            manager.deploy_workers()
            self.assertEqual(len(manager.workers), 2)
            print("  ✅ Workers deployed")

            # Monitor briefly
            print("\n👀 Monitoring workers...")
            time.sleep(2)

            # Get summary
            summary = manager.get_summary()
            print(f"\n📊 Summary: {summary['total_workers']} workers, {summary['active_workers']} active")
            self.assertEqual(summary['total_workers'], 2)

            # Shutdown
            print("\n🛑 Shutting down...")
            manager.shutdown()
            print("  ✅ Workers shut down")

            print("\n✅ Manager lifecycle test passed")

        finally:
            if workspace.exists():
                shutil.rmtree(workspace)


def _benchmark_task_1s(task_id):
    """Simulated 1-second task for benchmark suite"""
    time.sleep(1.0)
    return {"task_id": task_id, "duration": 1.0}


def run_benchmark_suite(num_workers_list: List[int] = [1, 2, 3, 5]):
    """
    Run comprehensive performance benchmark with varying worker counts

    Args:
        num_workers_list: List of worker counts to test
    """
    print("\n" + "="*80)
    print("PERFORMANCE BENCHMARK SUITE")
    print("="*80)

    num_tasks = 10
    results = []

    for num_workers in num_workers_list:
        print(f"\n📊 Testing with {num_workers} worker(s)...")

        start_time = time.time()

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(_benchmark_task_1s, task_id) for task_id in range(num_tasks)]
            task_results = [future.result() for future in as_completed(futures)]

        duration = time.time() - start_time
        speedup = (num_tasks * 1.0) / duration
        efficiency = speedup / num_workers if num_workers > 0 else 0

        results.append({
            "workers": num_workers,
            "duration": duration,
            "speedup": speedup,
            "efficiency": efficiency
        })

        print(f"  Duration: {duration:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Efficiency: {efficiency*100:.1f}%")

    # Print summary table
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)
    print(f"{'Workers':<10} {'Duration':<12} {'Speedup':<12} {'Efficiency'}")
    print("-"*80)

    for result in results:
        print(f"{result['workers']:<10} "
              f"{result['duration']:>8.2f}s    "
              f"{result['speedup']:>8.2f}x    "
              f"{result['efficiency']*100:>8.1f}%")

    print("="*80 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test parallel agent operations")

    parser.add_argument(
        "--test",
        help="Run specific test (e.g., test_concurrent_execution)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of workers for tests (default: 3)"
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmark suite"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Set worker count
    ParallelAgentTestSuite.num_workers = args.workers

    # Run benchmark if requested
    if args.benchmark:
        run_benchmark_suite()
        return

    # Run tests
    if args.test:
        # Run specific test
        suite = unittest.TestLoader().loadTestsFromName(
            f"__main__.ParallelAgentTestSuite.{args.test}"
        )
    else:
        # Run all tests
        suite = unittest.TestLoader().loadTestsFromTestCase(ParallelAgentTestSuite)
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ParallelIntegrationTests))

    runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
