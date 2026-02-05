import PyInstaller.__main__
import customtkinter
import os
import sys

# Get customtkinter path for data inclusion
ctk_path = os.path.dirname(customtkinter.__file__)

print(f"CustomTkinter path found: {ctk_path}")

# Build command arguments
args = [
    'main.py',                        # Main script
    '--name=ClipboardManager',        # Executable name
    '--onefile',                      # Single file
    '--noconsole',                    # No terminal window
    '--clean',                        # Clean cache
    f'--add-data={ctk_path}{os.pathsep}customtkinter', # Include CTk assets
    # Add other hidden imports if needed
    '--hidden-import=keyboard',
    '--hidden-import=pyperclip',
    '--hidden-import=PIL',            # CTk often needs PIL
    '--hidden-import=PIL._tkinter_finder',
]

print("Starting build process...")
PyInstaller.__main__.run(args)
print("Build complete! Check 'dist' folder.")
