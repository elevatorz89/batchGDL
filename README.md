# batchGDL
A simple TUI for managing gallery-dl subscriptions with a simple interface, written in python. It's recommended to be familiar with gallery-dl before using this script.

# Features
- Manage independent download lists and subscriptions independently of each other.
- An "append mode" that lets you redownload an entire subscription while ignoring the archive file. 
- Apply persistent flags per tab.
- Apply additional flags per download job.
- Search through your download job files from within the TUI.
- Shortcut buttons to config/log files.
- Update gallery-dl without using the command line.

# Installation
## Prerequisites
- Python 3.10+
- pip
- gallery-dl
- textual
- rapidfuzz

If you don't have pip installed, you can run the following command to install it manually:
```
python -m ensurepip --upgrade
```

The application will automatically install the below packages, but you can install them yourself by running:
```
python -m pip install rapidfuzz textual gallery-dl
```

## Setup
Download and unpack the zip file from the releases page. After doing so, edit the settings in the `batchGDL-config.json` file:

- `config_file` - Path to your gallery-dl config file. (include the file extension)
- `log_file` - Path to your gallery-dl logs file.
- `dl_folder` - Path to a folder to store your downloaded media.
- `oauth-sites` - A comma separated array of sites that require OAuth to download (protected) media.

By default, the file paths will point relative to the script folder.

## Running the script
Run the `run_windows.bat` or `run_linux-macos.sh` scripts to make it easier on desktop. Otherwise, run `batchGDL/main.py` in your terminal of choice.

On Linux/MacOS, you may need to run `chmod +x run_linux-macos.sh` to make the script executable.

## Updating
To update from an older version, replace the old `batchGDL` folder with the new one. Do not replace your config files.

# Gallery-DL Help
Refer to the official repositories for assistance and bugs related to the downloader and config file formatting:
- https://github.com/mikf/gallery-dl
- https://codeberg.org/mikf/gallery-dl

If a gallery-dl update fixes an issue, you can update it from the Config tab.

# FAQ
- What does the Append Tab do?
  - Append lists are used to add additional links to a subscription list; particularly to let you download everything from an account while ignoring date filters.
  - Each subscription has its own append list file so you can run multiple append jobs in parallel.
  - By default, append jobs will ignore items already in the archive file to avoid accidental downloads of duplicate media.
  - If you want to also ignore the subscription's archive file, you can toggle the "Ignore Archive" switch.
  - If you want to perform a one-off download of something specific, it's better to make a "Single" list and download using that instead.
- How do I restore a list from the trash?
  - Deleted lists are stored in your `lists/trash` folder.
  1. Move the list back to the single or subscriptions folder. 
  2. If you're restoring a subscriptions list, make sure to restore its append list (named `ap_[listname].txt`) as well.
  3. Then re-create the entry with the "Add List" button. Make sure that the list filename matches, or it won't relink.
- I can't download things from a particular site.
  - This is most likely an issue with gallery-dl. Try updating it from the Config tab, then file an issue on their [GitHub](https://github.com/mikf/gallery-dl) or [Codeberg](https://codeberg.org/mikf/gallery-dl) page if the issue persists.
  - Sometimes, sites may require you to provide cookies, an API key, or for you to log in using OAuth.
- How do I reorder my download jobs?
  - Your download jobs are based upon their ordering in the config file. Reorder them manually and refresh the config to see the changes. Reordering jobs from within the TUI may be a future feature if there's enough demand for it.