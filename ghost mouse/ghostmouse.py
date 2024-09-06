import json
import time
import threading
import tkinter as tk
from pynput import mouse, keyboard
from pynput.keyboard import Controller as KeyboardController, Key, Listener as KeyboardListener
import pyautogui

# Global variables
events = []
recording = False
replaying = False
start_time = 0
end_time = 0
recorded_duration = 0
original_duration = 0
mouse_listener = None
keyboard_listener = None
default_filename = "events.json"  # Default file for saving actions
toggle_key = Key.f10  # Default key for toggling recording
replay_key = Key.f9  # Default key for starting replay

# Function to update the countdown timer during replay
def update_countdown():
    global recorded_duration
    if replaying and recorded_duration > 0:
        minutes = int(recorded_duration // 60)
        seconds = int(recorded_duration % 60)
        timer_label.config(text=f"Replay Time: {minutes:02}:{seconds:02}")
        recorded_duration -= 1
        root.after(1000, update_countdown)  # Update every second
    elif replaying and recorded_duration <= 0:
        timer_label.config(text=f"Recorded Time: {int(original_duration // 60):02}:{int(original_duration % 60):02}")

# Function to toggle recording
def toggle_recording():
    global recording, start_time, end_time, recorded_duration, original_duration, mouse_listener, keyboard_listener

    if recording:
        # Stop recording
        recording = False
        end_time = time.time()
        recorded_duration = int(end_time - start_time)  # Calculate the total recorded duration
        original_duration = recorded_duration  # Store the original duration
        if mouse_listener is not None:
            mouse_listener.stop()
        if keyboard_listener is not None:
            keyboard_listener.stop()
        toggle_button.config(text="Start Recording", bg="green")
        replay_button.config(state="normal")  # Enable replay button
        toggle_key_button.config(state="normal")
        replay_key_button.config(state="normal")
        save_events()  # Automatically save after stopping recording

        # Display the recorded duration
        minutes = int(recorded_duration // 60)
        seconds = int(recorded_duration % 60)
        timer_label.config(text=f"Recorded Time: {minutes:02}:{seconds:02}")
    else:
        # Start recording
        events.clear()
        recording = True
        start_time = time.time()
        toggle_button.config(text="Stop Recording", bg="red")  # Allow stop recording
        replay_button.config(state="disabled")  # Disable replay button while recording
        toggle_key_button.config(state="disabled")
        replay_key_button.config(state="disabled")
        timer_label.config(text="Recording...")  # Indicate that recording is in progress

        def on_click(x, y, button, pressed):
            if pressed and not is_click_on_button(x, y):
                timestamp = time.time() - start_time
                events.append({'type': 'click', 'position': (x, y), 'timestamp': timestamp})

        def on_move(x, y):
            timestamp = time.time() - start_time
            events.append({'type': 'move', 'position': (x, y), 'timestamp': timestamp})

        def on_key_press(key):
            if key != toggle_key and key != replay_key:  # Ignore toggle and replay keys
                timestamp = time.time() - start_time
                events.append({'type': 'key_press', 'key': str(key), 'timestamp': timestamp})

        def on_key_release(key):
            if key != toggle_key and key != replay_key:  # Ignore toggle and replay keys
                timestamp = time.time() - start_time
                events.append({'type': 'key_release', 'key': str(key), 'timestamp': timestamp})

        # Start listeners
        mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
        mouse_listener.start()

        keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
        keyboard_listener.start()

def is_click_on_button(x, y):
    # Function to determine if the click is on any of the buttons to avoid recording these actions
    widget_under_click = root.winfo_containing(x, y)
    return widget_under_click in [toggle_button, replay_button, toggle_key_button, replay_key_button]

def save_events():
    # Save events to the default file without showing a notification
    with open(default_filename, 'w') as f:
        json.dump(events, f)

def replay_events():
    global replaying, recorded_duration
    if not events:
        messagebox.showwarning("Warning", "No events to replay!")
        return

    # Disable all functions except stopping replay
    replaying = True
    toggle_button.config(state="disabled")  # Prevent starting recording
    replay_button.config(state="normal")  # Keep enabled to allow stopping replay
    toggle_key_button.config(state="disabled")
    replay_key_button.config(state="disabled")

    # Set replay state and start countdown
    recorded_duration = original_duration  # Use the original recorded duration for the countdown
    update_countdown()  # Start the countdown

    def replay():
        pyautogui.PAUSE = 0
        keyboard = KeyboardController()
        replay_start = time.time()
        for event in events:
            while time.time() - replay_start < event['timestamp']:
                pass
            if event['type'] == 'move':
                pyautogui.moveTo(event['position'][0], event['position'][1], duration=0)
            elif event['type'] == 'click':
                pyautogui.click(event['position'][0], event['position'][1])
            elif event['type'] == 'key_press':
                key = event['key']
                try:
                    key = eval(key)
                except:
                    pass
                keyboard.press(key)
            elif event['type'] == 'key_release':
                key = event['key']
                try:
                    key = eval(key)
                except:
                    pass
                keyboard.release(key)
        
        # Re-enable buttons after replay
        toggle_button.config(state="normal")
        replay_button.config(state="normal")
        toggle_key_button.config(state="normal")
        replay_key_button.config(state="normal")
        replaying = False

    threading.Thread(target=replay).start()

# Function to handle the key press for toggling recording and starting replay
def on_key_press(key):
    if key == toggle_key and not replaying:  # Allow toggling recording but not during replay
        toggle_recording()
    elif key == replay_key and not recording:  # Allow starting replay but not during recording
        replay_events()

# Function to change the toggle or replay key
def change_key(action):
    # Directly wait for user input to set the new key
    def on_press(key):
        global toggle_key, replay_key
        if action == "toggle recording":
            toggle_key = key
            update_key_labels()
        elif action == "start replay":
            replay_key = key
            update_key_labels()
        settings_listener.stop()  # Stop the settings listener after setting the key

    # Start a temporary listener for selecting the new key
    settings_listener = KeyboardListener(on_press=on_press)
    settings_listener.start()

def update_key_labels():
    # Update the keybind display labels with the current key settings
    toggle_key_label.config(text=f"Recording Key: {toggle_key}")
    replay_key_label.config(text=f"Replay Key: {replay_key}")

# Set up the main application window
root = tk.Tk()
root.title("Ghost Mouse and Keyboard")
root.geometry("300x400")

# Create GUI buttons
toggle_button = tk.Button(root, text="Start Recording", bg="green", command=lambda: threading.Thread(target=toggle_recording).start())
replay_button = tk.Button(root, text="Replay Events", command=replay_events)
toggle_key_button = tk.Button(root, text="Set Toggle Key", command=lambda: change_key("toggle recording"))
replay_key_button = tk.Button(root, text="Set Replay Key", command=lambda: change_key("start replay"))

# Create a timer label
timer_label = tk.Label(root, text="Recording Time: 00:00")

# Create labels to display current keybinds
toggle_key_label = tk.Label(root, text=f"Recording Key: {toggle_key}")
replay_key_label = tk.Label(root, text=f"Replay Key: {replay_key}")

# Place buttons and labels in the window
toggle_button.pack(pady=10)
replay_button.pack(pady=10)
toggle_key_button.pack(pady=10)
replay_key_button.pack(pady=10)
timer_label.pack(pady=10)
toggle_key_label.pack(pady=5)
replay_key_label.pack(pady=5)

# Start a keyboard listener for the toggle and replay keys
keyboard_listener = KeyboardListener(on_press=on_key_press)
keyboard_listener.start()

# Run the main loop
root.mainloop()
