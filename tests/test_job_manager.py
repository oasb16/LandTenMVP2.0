import unittest
from superstructures.ss6_actionrelay.job_manager import create_job, assign_job, accept_job, reject_job

class TestJobManager(unittest.TestCase):

    def test_create_job(self):
        data = {
            "incident_id": "incident_123",
            "job_type": "Plumbing",
            "price": 150.0,
            "priority": "High",
            "description": "Fix leaking faucet"
        }
        job = create_job(data)
        self.assertEqual(job["job_type"], "Plumbing")
        self.assertEqual(job["price"], 150.0)

    def test_assign_job(self):
        job = create_job({
            "incident_id": "incident_123",
            "job_type": "Plumbing",
            "price": 150.0,
            "priority": "High",
            "description": "Fix leaking faucet"
        })
        assigned_job = assign_job(job["job_id"], "contractor_456")
        self.assertEqual(assigned_job["assigned_contractor_id"], "contractor_456")

    def test_accept_job(self):
        job = create_job({
            "incident_id": "incident_123",
            "job_type": "Plumbing",
            "price": 150.0,
            "priority": "High",
            "description": "Fix leaking faucet"
        })
        assign_job(job["job_id"], "contractor_456")
        accepted_job = accept_job(job["job_id"], "contractor_456")
        self.assertTrue(accepted_job["accepted"])
        self.assertEqual(accepted_job["status"], "accepted")

    def test_reject_job(self):
        job = create_job({
            "incident_id": "incident_123",
            "job_type": "Plumbing",
            "price": 150.0,
            "priority": "High",
            "description": "Fix leaking faucet"
        })
        assign_job(job["job_id"], "contractor_456")
        rejected_job = reject_job(job["job_id"], "contractor_456")
        self.assertFalse(rejected_job["accepted"])
        self.assertEqual(rejected_job["status"], "rejected")

if __name__ == "__main__":
    unittest.main()