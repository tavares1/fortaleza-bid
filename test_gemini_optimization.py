import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time

# Add app to path if not already there
sys.path.append(os.getcwd())

from app.services.gemini_service import GeminiService

class TestGeminiOptimization(unittest.TestCase):
    
    def setUp(self):
        # Mock Config to avoid needing real keys
        self.config_patcher = patch('app.services.gemini_service.Config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.GOOGLE_API_KEY = "fake_key"
        
        # Mock genai.Client
        self.genai_patcher = patch('app.services.gemini_service.genai')
        self.mock_genai = self.genai_patcher.start()
        
        # Mock time.sleep to run tests fast
        self.sleep_patcher = patch('app.services.gemini_service.time.sleep')
        self.mock_sleep = self.sleep_patcher.start()

        self.service = GeminiService()

    def tearDown(self):
        self.config_patcher.stop()
        self.genai_patcher.stop()
        self.sleep_patcher.stop()

    def test_text_model_rotation(self):
        """Test that it rotates through TEXT_MODELS on 429 error"""
        print("\n--- Testing Text Model Rotation ---")
        
        # Setup mock to raise exception for first 2 models, then succeed
        mock_generate = MagicMock()
        # Side effect: first 2 calls raise 429, 3rd returns success
        mock_generate.side_effect = [
            Exception("429 Resource Exhausted"),
            Exception("429 Resource Exhausted"),
            MagicMock(text="Success!")
        ]
        
        self.service.client.models.generate_content = mock_generate
        
        result = self.service._generate_with_retry(["test"], is_vision=False)
        
        self.assertEqual(result, "Success!")
        self.assertEqual(mock_generate.call_count, 3)
        # Verify it tried the first 3 models in TEXT_MODELS
        expected_models = self.service.TEXT_MODELS[:3]
        calls = mock_generate.call_args_list
        for i, call in enumerate(calls):
            self.assertEqual(call.kwargs['model'], expected_models[i])
            print(f"Call {i+1} used model: {call.kwargs['model']}")

    def test_vision_model_selection(self):
        """Test that is_vision=True uses VISION_MODELS"""
        print("\n--- Testing Vision Model Selection ---")
        
        mock_generate = MagicMock()
        mock_generate.return_value.text = "Vision Success"
        self.service.client.models.generate_content = mock_generate
        
        self.service._generate_with_retry(["image"], is_vision=True)
        
        # Should use first model of VISION_MODELS
        first_vision_model = self.service.VISION_MODELS[0]
        self.assertEqual(mock_generate.call_args.kwargs['model'], first_vision_model)
        print(f"Successfully used vision model: {first_vision_model}")

    def test_wait_after_exhaustion(self):
        """Test that it waits 60s after exhausting all models once"""
        print("\n--- Testing Wait Strategy ---")
        
        # We want to fail everything for the first cycle, then succeed on first of second cycle.
        # Number of models in list
        num_models = len(self.service.TEXT_MODELS)
        
        # Side effects: Fail (num_models) times, then Succeed
        side_effects = [Exception("429")] * num_models + [MagicMock(text="Finally worked")]
        
        mock_generate = MagicMock()
        mock_generate.side_effect = side_effects
        self.service.client.models.generate_content = mock_generate
        
        result = self.service._generate_with_retry(["test"], is_vision=False)
        
        self.assertEqual(result, "Finally worked")
        
        # Verify sleep was called with 60s
        self.mock_sleep.assert_any_call(60)
        print("Verified 60s sleep was triggered after exhausting all models.")

if __name__ == '__main__':
    unittest.main()
