import tkinter as tk
from pynput import keyboard
import threading
from pynput.keyboard import Key

class WordCountApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Word Counter")
        
        self.word_count = 0
        self.current_text = ""

        self.label = tk.Label(root, text="Word Count: 0", font=("Helvetica", 16))
        self.label.pack(pady=20)

        # Start listening to keyboard in a separate thread
        listener_thread = threading.Thread(target=self.start_listening)
        listener_thread.daemon = True  # Daemonize thread
        listener_thread.start()

    def update_label(self):
        self.label.after(0, lambda: self.label.config(text=f"Word Count: {self.word_count}"))

    def on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                self.current_text += key.char
            elif key == Key.space:  # Correctly handle the space key
                self.word_count += 1
                self.update_label()
        except AttributeError:
            pass

    def on_release(self, key):
        if key == keyboard.Key.esc:
            return False

    def start_listening(self):
        with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()

# Tkinter GUI setup
root = tk.Tk()
app = WordCountApp(root)
root.mainloop()
