from pynput import keyboard

current_text = ""
word_count = 0

def on_press(key):
    global current_text, word_count
    try:
        if key.char.isalpha() or key.char == ' ':
            current_text += key.char
            if key.char == ' ':
                word_count += 1
                print(f"Current word count: {word_count}")
    except AttributeError:
        pass  # Special keys like SHIFT, etc.

def on_release(key):
    if key == keyboard.Key.esc:
        # Stop listener
        print(f"Final word count: {word_count}")
        return False

with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()