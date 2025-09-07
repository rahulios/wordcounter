import tkinter as tk
from pynput import keyboard

import threading
from pynput.keyboard import Key

import pandas as pd
from datetime import datetime, timedelta

import os

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

        # Initialize label for yesterday's word count before calling load_previous_count
        self.previous_count_label = tk.Label(root, font=("Helvetica", 16))
        self.previous_count_label.pack(pady=10)

        # Now load the previous count
        self.load_previous_count()

        # Update the previous_count_label after loading the previous count
        self.previous_count_label.config(text=f"Yesterday's Word Count: {self.previous_count}")

        # Label for current word count
        self.current_count_label = tk.Label(root, text="Word Count: 0", font=("Helvetica", 16))
        self.current_count_label.pack(pady=10)

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
        if self.listener:
            self.listener.stop()
        self.listener_thread = None
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

        # Call the method to handle Excel file update
        self.update_excel_file()

        # Reset word count
        self.word_count = 0
        self.update_label()

    def update_excel_file(self):
        # Prepare new data
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        new_data = {'Date and Time': timestamp, 'Word Count': self.word_count}
        new_row = pd.DataFrame([new_data])

        # File path for the Excel file
        filename = "WordCountData.xlsx"

        # Read existing data if file exists, else create a new DataFrame
        if os.path.exists(filename):
            df = pd.read_excel(filename)
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = new_row

        # Ensure 'Date and Time' is a datetime column
        df['Date and Time'] = pd.to_datetime(df['Date and Time'])

        # Set 'Date and Time' as the DataFrame index
        df.set_index('Date and Time', inplace=True)

        # Now that 'Date and Time' is the index, we can perform the rolling operation without specifying 'on'
        df['Rolling 7-Day Avg'] = df['Word Count'].rolling(window='7D').mean()

        # Reset the index if you need 'Date and Time' as a column for Excel output
        df.reset_index(inplace=True)

        # Save updated DataFrame to Excel
        df.to_excel(filename, index=False)

    def load_previous_count(self):
        try:
            # Read data from Excel
            df = pd.read_excel("WordCountData.xlsx")

            # Ensure 'Date and Time' column is treated as datetime
            df['Date and Time'] = pd.to_datetime(df['Date and Time'])

            # Calculate yesterday's date
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_date_only = yesterday.date()

            # Filter rows where 'Date and Time' matches yesterday's date
            # Note: We're comparing only the date part to ignore time differences
            yesterdays_data = df[df['Date and Time'].dt.date == yesterday_date_only]

            if not yesterdays_data.empty:
                # If there's data for yesterday, use the last record's word count
                self.previous_count = yesterdays_data['Word Count'].iloc[-1]
            else:
                # If there's no data for yesterday, find the most recent entry before today
                most_recent_data = df[df['Date and Time'].dt.date < datetime.now().date()]
                if not most_recent_data.empty:
                    self.previous_count = most_recent_data['Word Count'].iloc[-1]
                else:
                    # No previous data found
                    self.previous_count = 0
        except Exception as e:
            print("Error loading previous count:", e)
            self.previous_count = 0

        # Update GUI to display previous count
        self.previous_count_label.config(text=f"Yesterday's Word Count: {self.previous_count}")

    
    def read_previous_count_from_file(self):
    # Your logic to read the previous day's count goes here
    # Return the count as an integer
    # For now, let's just return a dummy value, e.g., 100
        return 100

    def on_close(self):
        self.root.destroy()

# Tkinter GUI setup
root = tk.Tk()
app = WordCountApp(root)
root.mainloop()