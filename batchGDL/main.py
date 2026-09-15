import sys
import subprocess

if __package__ is None and not getattr(sys, 'frozen', False):
    # direct call of __main__.py
    import os.path
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))


from batchGDL.startup import check_dependencies, check_setup, mark_setup_complete, get_config_version
from batchGDL.config import reload_config
from batchGDL.constants import CONFIG_VERSION

if __name__ == "__main__":
    missing = check_dependencies()
    if missing:
        choice = ""
        while choice != "y" or "n":
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
        print("Make sure to open the readme and (if necessary) edit the first 5 lines in the batchGDL-config.json file before continuing.")
        input("Once you've made your edits, press ENTER to continue.")
        mark_setup_complete()
        reload_config()

    # get_config_version() # launches the config updater



    GdlTui().run()
