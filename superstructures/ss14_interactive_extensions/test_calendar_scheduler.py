import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from ss14_interactive_extensions import calendar_scheduler

class TestCalendarScheduler(unittest.TestCase):

    @patch("calendar_scheduler.build")
    @patch("calendar_scheduler.st")
    def test_schedule_event(self, mock_streamlit, mock_build):
        # Mock Streamlit inputs
        mock_streamlit.date_input.return_value = "2025-05-20"
        mock_streamlit.text_area.return_value = "Meeting with contractor"
        mock_streamlit.time_input.side_effect = ["10:00", "11:00"]
        mock_streamlit.button.return_value = True

        # Mock Google Calendar API
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.events().insert().execute.return_value = {"htmlLink": "http://example.com/event"}

        # Call the function
        calendar_scheduler()

        # Assertions
        mock_streamlit.success.assert_called_with("Event created: http://example.com/event")

if __name__ == "__main__":
    unittest.main()