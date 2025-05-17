import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from job_manager import JobManager

class TestJobManager(unittest.TestCase):

    def setUp(self):
        self.manager = JobManager()

    def test_create_job(self):
        job = self.manager.create_job("1", "Fix plumbing", "John", "2025-05-20")
        self.assertEqual(job["job_id"], "1")
        self.assertEqual(job["description"], "Fix plumbing")
        self.assertEqual(job["assignee"], "John")
        self.assertEqual(job["state"], "created")

    def test_assign_job(self):
        self.manager.create_job("1", "Fix plumbing", None, "2025-05-20")
        job = self.manager.assign_job("1", "John")
        self.assertEqual(job["assignee"], "John")
        self.assertEqual(job["state"], "assigned")

    def test_update_job_state(self):
        self.manager.create_job("1", "Fix plumbing", "John", "2025-05-20")
        job = self.manager.update_job_state("1", "in-progress")
        self.assertEqual(job["state"], "in-progress")

    def test_state_machine(self):
        self.manager.create_job("1", "Fix plumbing", "John", "2025-05-20")
        self.manager.state_machine("1", "assign")
        job = self.manager.get_job("1")
        self.assertEqual(job["state"], "assigned")
        self.manager.state_machine("1", "start")
        self.assertEqual(job["state"], "in-progress")
        self.manager.state_machine("1", "complete")
        self.assertEqual(job["state"], "completed")

if __name__ == "__main__":
    unittest.main()