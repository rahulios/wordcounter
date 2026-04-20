import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard
import threading
from pynput.keyboard import Key
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import Optional
import logging

class WordCountApp:
    def __init__(self, root: tk.Tk):
        """Initialize the WordCountApp with improved UI and functionality."""
        self.setup_logging()
        self.root = root
        self.configure_root()
        self.initialize_variables()
        self.create_ui()
        self.load_previous_count()
        self.setup_auto_save()

    def setup_logging(self) -> None:
        """Configure logging for the application."""
        logging.basicConfig(
            filename='word_counter.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def configure_root(self) -> None:
        """Configure the root window properties."""
        self.root.title("Word Counter Pro")
        self.root.geometry("600x400")
        self.root.minsize(500, 300)
        style = ttk.Style()
        style.theme_use('clam')  # or any other available theme

    def initialize_variables(self) -> None:
        """Initialize instance variables."""
        self.word_count = 0
        self.current_text = ""
        self.recording = False
        self.listener: Optional[keyboard.Listener] = None
        self.listener_thread: Optional[threading.Thread] = None
        self.previous_count = 0
        self.auto_save_interval = 300000  # 5 minutes in milliseconds

    def create_ui(self) -> None:
        """Create the user interface with improved layout and styling."""
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Statistics Frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="5")
        stats_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.current_count_label = ttk.Label(
            stats_frame, 
            text="Current Session: 0", 
            font=("Helvetica", 12)
        )
        self.current_count_label.grid(row=0, column=0, padx=5, pady=5)

        self.previous_count_label = ttk.Label(
            stats_frame,
            text="Yesterday's Count: 0",
            font=("Helvetica", 12)
        )
        self.previous_count_label.grid(row=0, column=1, padx=5, pady=5)

        # Control Buttons Frame
        control_frame = ttk.Frame(main_frame, padding="5")
        control_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(
            control_frame,
            text="Start Recording",
            command=self.start_recording
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.pause_button = ttk.Button(
            control_frame,
            text="Pause Recording",
            command=self.pause_recording,
            state=tk.DISABLED
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        self.stop_button = ttk.Button(
            control_frame,
            text="Stop Recording",
            command=self.stop_recording,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=2, padx=5)

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            length=200,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

    def update_word_count(self, key: keyboard.KeyCode) -> None:
        """Update word count based on keyboard input."""
        if not self.recording:
            return

        try:
            if hasattr(key, 'char') and key.char:
                self.current_text += key.char
            elif key in (Key.space, Key.enter):
                # Count word if there's text and we hit space or enter
                if self.current_text.strip():
                    self.word_count += 1
                    self.update_ui()
                self.current_text = ""
        except AttributeError as e:
            logging.error(f"Error processing key: {e}")

    def update_ui(self) -> None:
        """Update all UI elements."""
        self.current_count_label.config(text=f"Current Session: {self.word_count}")
        self.progress_var.set(min(self.word_count / 100 * 100, 100))  # Example progress calculation

    def start_recording(self) -> None:
        """Start the keyboard listener and recording process."""
        if not self.listener_thread or not self.listener_thread.is_alive():
            self.listener = keyboard.Listener(
                on_press=self.update_word_count,
                on_release=lambda key: None
            )
            self.listener_thread = threading.Thread(target=self.listener.start)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
        self.recording = True
        self.update_button_states(recording=True)
        logging.info("Recording started")

    def pause_recording(self) -> None:
        """Pause the recording process."""
        self.recording = False
        self.update_button_states(paused=True)
        logging.info("Recording paused")

    def stop_recording(self) -> None:
        """Stop recording and save the session."""
        self.recording = False
        if self.listener:
            self.listener.stop()
        self.listener_thread = None
        self.update_button_states()
        self.save_session()
        self.word_count = 0
        self.update_ui()
        logging.info("Recording stopped and session saved")

    def update_button_states(self, recording: bool = False, paused: bool = False) -> None:
        """Update button states based on recording status."""
        self.start_button.config(state=tk.DISABLED if recording else tk.NORMAL)
        self.pause_button.config(state=tk.NORMAL if recording else tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL if recording or paused else tk.DISABLED)

    def save_session(self) -> None:
        """Save the current session data to Excel."""
        try:
            filename = "WordCountData.xlsx"
            now = datetime.now()
            new_data = {
                'Date and Time': [now.strftime("%Y-%m-%d %H:%M:%S")],
                'Word Count': [self.word_count]
            }
            new_df = pd.DataFrame(new_data)

            if os.path.exists(filename):
                df = pd.read_excel(filename)
                df = pd.concat([df, new_df], ignore_index=True)
            else:
                df = new_df

            df['Date and Time'] = pd.to_datetime(df['Date and Time'])
            df.set_index('Date and Time', inplace=True)
            df['Rolling 7-Day Avg'] = df['Word Count'].rolling(window='7D').mean()
            df.reset_index(inplace=True)
            df.to_excel(filename, index=False)
            
            logging.info(f"Session saved successfully: {self.word_count} words")
        except Exception as e:
            logging.error(f"Error saving session: {e}")
            messagebox.showerror("Error", "Failed to save session data")

    def load_previous_count(self) -> None:
        """Load and display the previous day's word count."""
        try:
            if not os.path.exists("WordCountData.xlsx"):
                return

            df = pd.read_excel("WordCountData.xlsx")
            df['Date and Time'] = pd.to_datetime(df['Date and Time'])
            yesterday = datetime.now().date() - timedelta(days=1)
            
            yesterdays_data = df[df['Date and Time'].dt.date == yesterday]
            if not yesterdays_data.empty:
                self.previous_count = yesterdays_data['Word Count'].sum()
            else:
                recent_data = df[df['Date and Time'].dt.date < datetime.now().date()]
                if not recent_data.empty:
                    self.previous_count = recent_data.iloc[-1]['Word Count']

            self.previous_count_label.config(text=f"Yesterday's Count: {self.previous_count}")
            logging.info(f"Previous count loaded: {self.previous_count}")
        except Exception as e:
            logging.error(f"Error loading previous count: {e}")
            messagebox.showwarning("Warning", "Could not load previous count")

    def setup_auto_save(self) -> None:
        """Configure automatic saving of session data."""
        def auto_save():
            if self.recording and self.word_count > 0:
                self.save_session()
            self.root.after(self.auto_save_interval, auto_save)
        
        self.root.after(self.auto_save_interval, auto_save)

    def on_close(self) -> None:
        """Handle application closure."""
        if self.recording:
            if messagebox.askyesno("Confirm Exit", "Recording is in progress. Save before exiting?"):
                self.stop_recording()
        self.root.destroy()

def main():
    """Main entry point for the application."""
    try:
        root = tk.Tk()
        app = WordCountApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Application failed to start: {e}")
        raise

if __name__ == "__main__":
    main()