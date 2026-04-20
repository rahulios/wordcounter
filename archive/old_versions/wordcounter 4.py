import tkinter as tk
from pynput import keyboard

import threading
from pynput.keyboard import Key

import pandas as pd
from datetime import datetime, timedelta

import json
from datetime import datetime

class WordCountApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Word Counter")
        
        self.root.geometry("500x300")

        self.word_count = 0
        self.current_text = ""

        self.label = tk.Label(root, text="Word Count: 0", font=("Helvetica", 16))
        self.label.pack(pady=20)

        # Buttons for controlling recording
        self.start_button = tk.Button(root, text="Start Recording", command=self.start_recording)
        self.start_button.pack()

        self.pause_button = tk.Button(root, text="Pause Recording", command=self.pause_recording, state=tk.DISABLED)
        self.pause_button.pack()

        self.stop_button = tk.Button(root, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack()

        self.listener = None
        self.listener_thread = None
        self.recording = False

        self.previous_count = 0  # Variable to store yesterday's word count
        self.load_previous_count()

        # Label for current word count
        self.current_count_label = tk.Label(root, text="Word Count: 0", font=("Helvetica", 16))
        self.current_count_label.pack(pady=10)

        # Label for yesterday's word count
        self.previous_count_label = tk.Label(root, text=f"Yesterday's Word Count: {self.previous_count}", font=("Helvetica", 16))
        self.previous_count_label.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_label(self):
        self.label.after(0, lambda: self.label.config(text=f"Word Count: {self.word_count}"))

    def on_press(self, key):
        if self.recording:
            try:
                if hasattr(key, 'char') and key.char:
                    self.current_text += key.char
                elif key == Key.space:
                    self.word_count += 1
                    self.update_label()
            except AttributeError:
                pass

    def on_release(self, key): 
        pass # removing for now as we have a stop recording feature

    def start_listening(self):
        with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release) as self.listener:
            self.listener.join()

    def start_recording(self):
        if not self.listener_thread or not self.listener_thread.is_alive():
            self.listener_thread = threading.Thread(target=self.start_listening)
            self.listener_thread.daemon = True
            self.listener_thread.start()
        self.recording = True
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)

    def pause_recording(self):
        self.recording = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)

    def stop_recording(self):
        self.recording = False
        self.listener.stop()  # Stops the listener
        self.listener_thread = None
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

        # Exporting data to Excel
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        data = {'Date and Time': [timestamp], 'Word Count': [self.word_count]}
        df = pd.DataFrame(data)
        filename = f"WordCount_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)

        # Resetting word count
        self.word_count = 0
        self.update_label()

    def update_current_count_label(self):
        # Update the label for current word count
        self.current_count_label.config(text=f"Word Count: {self.word_count}")

    def load_previous_count(self):
        try:
            # Read data from Excel
            df = pd.read_excel("WordCountData.xlsx")

            # Calculate yesterday's date
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            # Check if there's data for yesterday
            yesterdays_data = df[df['Date and Time'].str.startswith(yesterday)]

            if not yesterdays_data.empty:
                # If there's data for yesterday, use it
                self.previous_count = yesterdays_data['Word Count'].iloc[-1]
            else:
                # If there's no data for yesterday, find the most recent entry including today
                df['Date and Time'] = pd.to_datetime(df['Date and Time'])
                most_recent = df[df['Date and Time'] <= pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))]
                if not most_recent.empty:
                    self.previous_count_label.config(text=f"Yesterday's Word Count: {self.previous_count}")
                else:
                    self.previous_count = 0

            # Update GUI to display previous count, if needed
        except Exception as e:
            print("Error loading previous count:", e)
            self.previous_count = 0
            self.previous_count_label.config(text="Yesterday's Word Count: 0")
    
    def read_previous_count_from_file(self):
    # Your logic to read the previous day's count goes here
    # Return the count as an integer
    # For now, let's just return a dummy value, e.g., 100
        return 100

    def save_current_count(self):
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {'Date and Time': [today], 'Word Count': [self.word_count]}
        df = pd.DataFrame(data)

        try:
            # Append if the file already exists
            with open("WordCountData.xlsx", "rb") as f:
                df_existing = pd.read_excel(f)
                df = pd.concat([df_existing, df], ignore_index=True)

        except FileNotFoundError:
            pass  # If file doesn't exist, we create a new one

        df.to_excel("WordCountData.xlsx", index=False)

    def on_close(self):
        self.save_current_count()
        self.root.destroy()

# Tkinter GUI setup
root = tk.Tk()
app = WordCountApp(root)
root.mainloop()