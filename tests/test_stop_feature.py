import threading
import time
from unittest.mock import patch
from services.voice_service import process_command
from util.command_interrupt import set_stop_requested, reset_stop_requested, is_stop_requested
from util.logger import logger

def mocked_interruptible_api_call(*args, **kwargs):
    """
    This mock function simulates a long-running API call that is interruptible.
    It checks for the stop_requested flag periodically.
    This is used for services like GPT that we imagine could be internally interruptible.
    """
    logger.info("MOCK API: Call started. Will run for up to 10 seconds.")
    for i in range(10):
        if is_stop_requested():
            logger.info("MOCK API: Stop request detected, aborting call.")
            return "Command stopped by user."
        logger.info(f"MOCK API: Processing... ({i + 1}/10)")
        time.sleep(1)
    logger.info("MOCK API: Call finished without interruption.")
    return "This is a mock response from a long API call."

def slow_service_mock(response_data, service_name="Service"):
    """
    This mock function simulates a slow, non-interruptible API call.
    It sleeps for a fixed duration and then returns a predefined response.
    This is used for testing if the command flow stops *after* a long call.
    """
    def mock_func(*args, **kwargs):
        logger.info(f"MOCK {service_name}: Call started. Simulating a 5-second network delay.")
        time.sleep(5)
        logger.info(f"MOCK {service_name}: Call finished.")
        return response_data
    return mock_func

def run_test(command, target_to_patch, mock_function):
    """
    Runs a test case by patching a target function with a given mock.
    """
    logger.info(f"\n--- Testing command: '{command}' ---")
    reset_stop_requested()

    result_container = []
    def command_runner():
        # process_command will call our patched function
        response = process_command(command)
        result_container.append(response)

    # We replace the real API call with our mock version
    with patch(target_to_patch, new=mock_function):
        command_thread = threading.Thread(target=command_runner)
        command_thread.start()

        logger.info("Test thread started. Waiting 3 seconds before interrupting.")
        time.sleep(3)

        logger.info(">>> Simulating stop command via set_stop_requested(True) <<<")
        set_stop_requested(True)

        command_thread.join(timeout=5) # Wait for the thread to complete

    if command_thread.is_alive():
        logger.error("❌ TEST FAILED: Command thread is still running.")
    else:
        final_result = result_container[0] if result_container else "No result"
        if "Command stopped by user" in final_result:
            logger.info(f"✅ TEST PASSED: Command was successfully interrupted. Final result: '{final_result}'")
        else:
            logger.error(f"❌ TEST FAILED: Command was not interrupted. Final result: '{final_result}'")

if __name__ == "__main__":
    logger.info("Starting mock command tests for the stop feature.")
    logger.info("This test script mocks long-running API calls to test the interruption mechanism without needing real API keys.")

    # Test case for a command that uses the GPT service (interruptible mock)
    # run_test(
    #     command="tell me a story",
    #     target_to_patch="services.voice_service.chat_with_gpt",
    #     mock_function=mocked_interruptible_api_call
    # )

    # Test case for the Weather service (non-interruptible mock)
    run_test(
        command="weather",
        target_to_patch="services.voice_service.get_weather",
        mock_function=slow_service_mock(
            {'weather': [{'description': 'mocked weather'}], 'main': {'temp': 0}},
            service_name="Weather"
        )
    )

    # Test case for the News service (non-interruptible mock)
    run_test(
        command="news",
        target_to_patch="services.voice_service.get_news",
        mock_function=slow_service_mock(
            {'articles': [{'title': 'mocked news'}]},
            service_name="News"
        )
    )

    # Test case for the Crypto service (non-interruptible mock)
    run_test(
        command="crypto",
        target_to_patch="services.voice_service.get_crypto_prices",
        mock_function=slow_service_mock(
            {'bitcoin': '0', 'ethereum': '0'},
            service_name="Crypto"
        )
    )

    # --- Real API Test ---
    # This part will make a real call to the OpenAI API.
    # Make sure your .env file has a valid OPENAI_API_KEY.
    logger.info("\n--- Testing REAL OpenAI API Call ---")
    reset_stop_requested() # Reset flag before the test
    real_command = "Tell me joke"
    logger.info(f"Sending command to process_command: '{real_command}'")
    # The `process_command` function will call the real `chat_with_gpt`.
    real_response = process_command(real_command)
    logger.info(f"Response from OpenAI: {real_response}")

    if not real_response or "couldn't process" in real_response or "stopped by user" in real_response:
        logger.error("❌ REAL API TEST FAILED: Check your OPENAI_API_KEY in .env and internet connection.")
    else:
        logger.info("✅ REAL API TEST PASSED: Successfully received a response.") 