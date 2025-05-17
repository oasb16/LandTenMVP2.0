class JobManager:
    def __init__(self):
        self.jobs = []

    def create_job(self, job_id, description, assignee, deadline):
        job = {
            "job_id": job_id,
            "description": description,
            "assignee": assignee,
            "deadline": deadline,
            "state": "created"
        }
        self.jobs.append(job)
        return job

    def assign_job(self, job_id, assignee):
        for job in self.jobs:
            if job["job_id"] == job_id:
                job["assignee"] = assignee
                job["state"] = "assigned"
                return job
        return None

    def update_job_state(self, job_id, new_state):
        valid_states = ["created", "assigned", "in-progress", "completed"]
        if new_state not in valid_states:
            raise ValueError(f"Invalid state: {new_state}")

        for job in self.jobs:
            if job["job_id"] == job_id:
                job["state"] = new_state
                return job
        return None

    def get_job(self, job_id):
        for job in self.jobs:
            if job["job_id"] == job_id:
                return job
        return None

    def list_jobs(self):
        return self.jobs

    def state_machine(self, job_id, action):
        transitions = {
            "created": ["assign"],
            "assigned": ["start"],
            "in-progress": ["complete"],
            "completed": []
        }

        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")

        current_state = job["state"]
        if action not in transitions[current_state]:
            raise ValueError(f"Action '{action}' is not valid for state '{current_state}'.")

        new_state = {
            "assign": "assigned",
            "start": "in-progress",
            "complete": "completed"
        }.get(action)

        if new_state:
            self.update_job_state(job_id, new_state)
            return job

        return None