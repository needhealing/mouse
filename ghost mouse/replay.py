import pyautogui
import time
import json
from pynput.keyboard import Controller as KeyboardController, Key

# Load recorded events
with open('events.json', 'r') as f:
    events = json.load(f)

# Initialize PyAutoGUI and keyboard controller
pyautogui.PAUSE = 0
keyboard = KeyboardController()

# Replay events using timestamps
start_time = time.time()
for event in events:
    # Wait until the actual time for the event
    while time.time() - start_time < event['timestamp']:
        pass  # Busy-waiting until it's time to perform the action

    if event['type'] == 'move':
        pyautogui.moveTo(event['position'][0], event['position'][1], duration=0)
    elif event['type'] == 'click':
        pyautogui.click(event['position'][0], event['position'][1])
    elif event['type'] == 'key_press':
        key = event['key']
        # Convert key from string format back to Key object if needed
        try:
            key = eval(key)
        except:
            pass
        keyboard.press(key)
    elif event['type'] == 'key_release':
        key = event['key']
        # Convert key from string format back to Key object if needed
        try:
            key = eval(key)
        except:
            pass
        keyboard.release(key)

print("Replay completed.")
