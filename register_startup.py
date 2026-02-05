import os
import subprocess

def add_to_startup():
    # Target Executable
    exe_path = os.path.abspath(r"dist\ClipboardManager.exe")
    
    # Startup Folder
    startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_folder, "ClipboardManager.lnk")
    
    if not os.path.exists(exe_path):
        print(f"Error: Executable not found at {exe_path}")
        print("Please run 'python build.py' first.")
        return

    print(f"Target EXE: {exe_path}")
    print(f"Startup Dir: {startup_folder}")

    # Use VBScript to create shortcut (Standard Windows method, no extra libs needed)
    vbs_content = f"""
    Set oWS = WScript.CreateObject("WScript.Shell")
    sLinkFile = "{shortcut_path}"
    Set oLink = oWS.CreateShortcut(sLinkFile)
    oLink.TargetPath = "{exe_path}"
    oLink.WorkingDirectory = "{os.path.dirname(exe_path)}"
    oLink.Description = "Clipboard Manager Auto-Run"
    oLink.Save
    """
    
    vbs_file = "create_shortcut_temp.vbs"
    try:
        with open(vbs_file, "w") as f:
            f.write(vbs_content)
        
        # Execute VBS
        subprocess.run(["cscript", "//Nologo", vbs_file], check=True)
        print("✅ Successfully added to Windows Startup!")
        print("The app will now launch automatically when you restart your PC.")
    
    except Exception as e:
        print(f"❌ Failed to create shortcut: {e}")
    finally:
        if os.path.exists(vbs_file):
            os.remove(vbs_file)

if __name__ == "__main__":
    add_to_startup()
