import os
import sys
import subprocess

_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__))))
if __package__ is None and not getattr(sys, "frozen", False):
    # direct call of main.py
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)


from batchGDL.startup import check_dependencies, check_setup, mark_setup_complete, get_config_version
from batchGDL.config import reload_config

if __name__ == "__main__":
    missing = check_dependencies()
    if missing:
        choice = ""
        while choice not in ("y", "n"):
            choice = input("Would you like to install the missing dependencies? (Y/n) ").lower()
            if choice == "y":
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--break-system-packages", *missing]
                )
                break
            elif choice == "n":
                exit(0)

    from batchGDL.app import GdlTui

    if not check_setup():
        print("\n---")
        print("Make sure to read the readme and config-help.md, then edit batchGDL-config.json before continuing.")
        input("Once you've made your edits, press ENTER to continue.")
        reload_config()
        mark_setup_complete()
        

    get_config_version() # launches the config updater



    GdlTui().run()
