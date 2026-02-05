import os
import sys
import subprocess

def get_executable_path():
    """
    Returns the absolute path to the executable or script.
    """
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(sys.argv[0])

def add_to_startup():
    """
    Adds the current application to Windows Startup using a shortcut.
    """
    exe_path = get_executable_path()
    
    # Check if running as script (dev mode) or frozen exe
    if not getattr(sys, 'frozen', False):
        # In dev mode, we might not want to register specific temp scripts, 
        # but for verifying the logic, we can point to the python interpreter or just warn.
        # For this specific app, let's point to the dist location if it exists, or skip.
        # Actually, let's just use the current script for testing awareness.
        print("Running in dev mode. Startup registration might not work as expected for end users unless compiled.")
    
    startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_folder, "ClipboardManager.lnk")
    
    # Use VBScript to create shortcut
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
        
        subprocess.run(["cscript", "//Nologo", vbs_file], check=True)
        return True
    except Exception as e:
        print(f"Failed to create shortcut: {e}")
        return False
    finally:
        if os.path.exists(vbs_file):
            os.remove(vbs_file)

def remove_from_startup():
    """
    Removes the application from Windows Startup.
    """
    startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_folder, "ClipboardManager.lnk")
    
    if os.path.exists(shortcut_path):
        try:
            os.remove(shortcut_path)
            return True
        except Exception as e:
            print(f"Failed to remove shortcut: {e}")
            return False
    return True # Already removed
