import unittest
from unittest.mock import patch, call
import time
import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.voice_service import wait_for_wake_and_command

class TestAuthenticationFlow(unittest.TestCase):

    def setUp(self):
        """Disable logging for this test class."""
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Re-enable logging after the test class."""
        logging.disable(logging.NOTSET)

    @patch('services.voice_service.wake_word_detected')
    @patch('services.voice_service.recognize_faces_vocally')
    @patch('services.voice_service.speak_response')
    @patch('services.voice_service.listen_command')
    @patch('services.voice_service.load_known_faces')
    @patch('services.voice_service.set_active_profile')
    @patch('time.time')
    @patch('services.user_profile_service.get_user_profile')
    def test_authentication_flow(
        self, mock_get_user_profile, mock_time, mock_set_active_profile, 
        mock_load_known_faces, mock_listen_command, mock_speak_response, 
        mock_recognize_faces, mock_wake_word
    ):
        # --- Mock Setup ---
        mock_wake_word.side_effect = [True, True, True, True, True, False]
        mock_time.side_effect = [
            1000, # Ghost
            1100, # Alex (session starts)
            1200, # Unknown
            2200, # Alex (session has timed out)
            2300, # Alex (within new session, no recognition needed)
            2301, 2302, 2303, 2304, 2305, 2306, 2307, 2308, 2309, 2310,
            2311, 2312, 2313, 2314, 2315, 2316, 2317, 2318, 2319, 2320,
            2321, 2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2330
        ]
                                 
        mock_recognize_faces.side_effect = ["ghost", "Alex", "Unknown", "Alex"]
        # Provide enough listen commands to prevent StopIteration
        mock_listen_command.side_effect = [
            "yes", "command 1", "that's all", # For Alex's first session
            "no", "command 2", "that's all", # For Unknown's session
            "yes", "command 3", "that's all",  # For Alex's second session
            "that's all", "that's all", "that's all", "that's all"
        ]
        mock_load_known_faces.return_value = {"Alex": "some_encoding"}
        
        # Mock profile loading
        alex_profile = {"name": "Alex", "preferences": {}}
        unknown_profile = {"name": "unknown", "preferences": {}}
        mock_get_user_profile.side_effect = [alex_profile, unknown_profile, alex_profile]

        # --- Run Function ---
        wait_for_wake_and_command()

        # --- Assertions ---
        # Recognition should be called 4 times: ghost, Alex, Unknown, and Alex again after timeout.
        # It is NOT called the 5th time because Alex is already known from the 4th interaction.
        self.assertEqual(mock_recognize_faces.call_count, 4)

        # Verify spoken responses
        speak_calls = [c[0][0] for c in mock_speak_response.call_args_list]
        
        self.assertIn("Must have been the wind.", speak_calls)
        self.assertIn("I don't recognize you. Would you like to register?", speak_calls)
        self.assertEqual(speak_calls.count("Hello Alex, ready to start?"), 2, "Should greet Alex twice")

        # Verify user profiles are set correctly
        # Called for Alex, then Unknown, then Alex again after timeout.
        self.assertEqual(mock_set_active_profile.call_count, 3)
        set_profile_calls = mock_set_active_profile.call_args_list
        self.assertEqual(set_profile_calls[0][0][0]['name'], 'Alex')
        self.assertEqual(set_profile_calls[1][0][0]['name'], 'unknown')
        self.assertEqual(set_profile_calls[2][0][0]['name'], 'Alex')

if __name__ == '__main__':
    unittest.main() 