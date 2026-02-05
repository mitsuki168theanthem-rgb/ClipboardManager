import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import keyboard
import threading
import socket
import sys
import queue
import logging
import traceback
import json
import os
from ui import MainWindow, SaveWindow
from clipboard_manager import ClipboardManager
import utils

# Setup logging
logging.basicConfig(
    filename='app.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

class ClipboardApp:
    def __init__(self):
        try:
            self.enforce_single_instance()
            self.clipboard_manager = ClipboardManager()
            
            # Queue for thread-safe communication
            self.event_queue = queue.Queue()
            
            self.app = MainWindow(on_paste_callback=self.paste_template, on_edit_callback=self.edit_template_action)
            self.app.withdraw() # Start hidden
            
            # Initialize SaveWindow persistent instance
            self.save_window = SaveWindow(self.app, on_save_callback=self.app.refresh_list)
            self.save_window.withdraw()

            # First Run Check
            self.check_first_run()

            # Hotkeys
            self.PASTE_HOTKEY = 'alt+v'
            self.SAVE_HOTKEY = 'ctrl+shift+s'
            
            # Use lambda to put events in queue, avoiding direct GUI calls from thread
            keyboard.add_hotkey(self.PASTE_HOTKEY, lambda: self.event_queue.put("show_paste"))
            keyboard.add_hotkey(self.SAVE_HOTKEY, lambda: self.event_queue.put("show_save"))
            
            print(f"App running... Hotkeys: Paste=[{self.PASTE_HOTKEY}], Save=[{self.SAVE_HOTKEY}]")
            
            # Start checking queue
            self.check_queue()
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            logging.error(traceback.format_exc())
            raise e

    def enforce_single_instance(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(('127.0.0.1', 45678)) # Arbitrary port
        except socket.error:
            print("⚠️ ERROR: The application is already running!")
            print("Please close the existing instance (or hidden process) first.")
            if sys.stdin and sys.stdout: # Only exit if run interactively, though logging catches it
                 sys.exit(1)
            else:
                 sys.exit(1)

    def check_first_run(self):
        config_file = "config.json"
        
        # Load or Create Config
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except:
                config = {}
        else:
            config = {}

        # Check if first run
        if not config.get("setup_completed"):
            # Show dialog
            # Create a hidden root for the messagebox if app is not shown yet
            # self.app is a CTk window, but it's withdrawn. MessageBox should work fine with it as parent or None.
            # Using standard tkinter messagebox for simplicity and reliability in system dialogs
            
            # Make sure main window is initialized enough to be a parent, or use a temporary hidden root
            # Since self.app exists (created in __init__), we can use it.
            
            response = messagebox.askyesno(
                "Initial Setup", 
                "Do you want to start this application automatically when Windows starts?"
            )
            
            if response:
                if utils.add_to_startup():
                    messagebox.showinfo("Success", "Added to startup!")
                    config["auto_start"] = True
                else:
                    messagebox.showerror("Error", "Failed to add to startup.")
                    config["auto_start"] = False
            else:
                config["auto_start"] = False
            
            config["setup_completed"] = True
            
            # Save config
            try:
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
            except Exception as e:
                logging.error(f"Failed to save config: {e}")
    
    def check_queue(self):
        try:
            while True:
                event = self.event_queue.get_nowait()
                # Handle tuple event
                if isinstance(event, tuple):
                    event_type, data = event
                    self.process_event(event_type, data)
                else:
                    self.process_event(event)
        except queue.Empty:
            pass
        except Exception as e:
            logging.error(f"Queue processing error: {e}")
            logging.error(traceback.format_exc())
        finally:
            # Check again in 100ms
            self.app.after(100, self.check_queue)

    def process_event(self, event_type, data=None):
        try:
            if event_type == "show_paste":
                self.app.reset_and_show()
            elif event_type == "show_save":
                self.show_save_window_action()
            elif event_type == "edit_save":
                self.show_edit_window_action(data)
        except Exception as e:
             logging.error(f"Event processing error ({event_type}): {e}")
             logging.error(traceback.format_exc())

    def show_save_window_action(self):
        try:
            content = self.clipboard_manager.get_clipboard_text()
            
            # Use persistent window, recreate only if dead
            try:
                self.save_window.winfo_exists()
            except (tk.TclError, AttributeError):
                 self.save_window = SaveWindow(self.app, on_save_callback=self.app.refresh_list)
            
            # Reset callbacks for normal save mode (just close on finish)
            self.save_window.on_save_callback = self.app.refresh_list
            self.save_window.on_cancel_callback = None

            self.save_window.reset_and_show(content)
            
            # Force focus
            self.save_window.after(100, self.save_window.lift)
            self.save_window.after(100, self.save_window.focus_force)
            
        except Exception as e:
            logging.error(f"Error checking queue action: {e}")

    def show_edit_window_action(self, item):
         try:
            # Close main window first? Preferable.
            self.app.withdraw()

            try:
                self.save_window.winfo_exists()
            except (tk.TclError, AttributeError):
                 self.save_window = SaveWindow(self.app, on_save_callback=self.app.refresh_list)

            # Set callbacks to reopen main window after edit/cancel
            def on_edit_finished():
                self.app.refresh_list()
                self.app.reset_and_show()

            self.save_window.on_save_callback = on_edit_finished
            self.save_window.on_cancel_callback = self.app.reset_and_show

            self.save_window.reset_and_show(
                content=item['content'],
                template_id=item['id'],
                title=item['title'],
                category=item['category']
            )
            
            self.save_window.after(100, self.save_window.lift)
            self.save_window.after(100, self.save_window.focus_force)
            
         except Exception as e:
            logging.error(f"Error showing edit window: {e}")

    def edit_template_action(self, item):
        self.event_queue.put(("edit_save", item))

    def paste_template(self, text):
        # This is called from the GUI thread
        try:
            self.app.update() 
            self.clipboard_manager.paste_text(text)
        except Exception as e:
            logging.error(f"Paste error: {e}")

    def run(self):
        try:
            # If start hidden, we don't necessarily show app, but we run the loop.
            # But the MessageBox in __init__ needs to be handled before or during loop?
            # Creating messagebox in __init__ blocks execution until closed, which is fine for startup check.
            self.app.mainloop()
        except Exception as e:
             logging.critical(f"Main loop crashed: {e}")
             logging.critical(traceback.format_exc())

if __name__ == "__main__":
    try:
        app = ClipboardApp()
        app.run()
    except Exception as e:
        logging.critical(f"Application failed to start: {e}")
        logging.critical(traceback.format_exc())
