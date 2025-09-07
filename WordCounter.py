# WordCounter.py

import tkinter as tk

def update_word_count(event=None):
    text = text_input.get("1.0", "end-1c")
    word_count = len(text.split())
    word_count_label.config(text=f"Word Count: {word_count}")

# Set up the main window
root = tk.Tk() # setting up a basic tkinter window 
root.title("Real-Time Word Count Tracker") # adding a name to the window 

# Create a Text widget
text_input = tk.Text(root, height=10, width=50)
text_input.pack()

# Bind the Text widget to update the word count on any change
text_input.bind("<KeyRelease>", update_word_count)

# Label to display the word count
word_count_label = tk.Label(root, text="Word Count: 0")
word_count_label.pack()

# Start the GUI event loop
root.mainloop()