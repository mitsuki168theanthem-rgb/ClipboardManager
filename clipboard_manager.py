import pyperclip
import keyboard
import time

class ClipboardManager:
    def __init__(self):
        pass

    def get_clipboard_text(self):
        return pyperclip.paste()

    def set_clipboard_text(self, text):
        pyperclip.copy(text)

    def paste_text(self, text):
        """
        Sets the text to clipboard and simulates Ctrl+V.
        """
        original = self.get_clipboard_text()
        try:
            self.set_clipboard_text(text)
            # Short delay to ensure clipboard is updated
            time.sleep(0.1)
            keyboard.send('ctrl+v')
            # Restore original clipboard? Maybe optional, but user might want to keep the pasted item.
            # For this utility, usually we want the pasted item to remain or maybe not.
            # Let's keep it simple: just paste.
        except Exception as e:
            print(f"Error pasting text: {e}")
        finally:
            pass
