import unittest
from superstructures.ss6_actionrelay.incident_manager import create_incident

class TestIncidentManager(unittest.TestCase):

    def test_create_valid_incident(self):
        data = {
            "tenant_id": "tenant_123",
            "property_id": "property_456",
            "issue": "Leaking faucet",
            "priority": "High",
            "chat_data": []
        }
        incident = create_incident(data)
        self.assertEqual(incident["tenant_id"], "tenant_123")
        self.assertEqual(incident["priority"], "High")

    def test_missing_fields(self):
        data = {
            "tenant_id": "tenant_123",
            "property_id": "property_456",
            "priority": "High",
            "chat_data": []
        }
        with self.assertRaises(ValueError):
            create_incident(data)

    def test_invalid_chat_data_type(self):
        data = {
            "tenant_id": "tenant_123",
            "property_id": "property_456",
            "issue": "Leaking faucet",
            "priority": "High",
            "chat_data": "This should be a list"
        }
        with self.assertRaises(ValueError):
            create_incident(data)

if __name__ == "__main__":
    unittest.main()