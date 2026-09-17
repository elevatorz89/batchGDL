# batchGDL
A simple TUI for managing gallery-dl subscriptions with a simple interface, written in python. It's recommended to be familiar with gallery-dl before using this script.

# Features
- Manage independent download lists and subscriptions independently of each other.
- An "append mode" that lets you redownload an entire subscription while ignoring the archive file. 
- Apply additional flags per download job
- Search through your download job files from within the TUI.
- Shortcut buttons to config/log files.
- Update gallery-dl without using the command line.

# Installation
## Prerequisites
- Python 3.10+
- gallery-dl
- textual
- rapidfuzz

```
python -m pip install rapidfuzz textual gallery-dl
```

## Setup
Download and unpack the zip file from the releases page. After doing so, edit the settings in the `batchGDL-config.json` file:

- `config_file` - Path to your gallery-dl config file. (include the file extension)
- `log_file` - Path to your gallery-dl logs file.
- `dl_folder` - Path to a folder to store your downloaded media.
- `oauth-sites` - A comma separated list of sites that require OAuth to download (protected) media.

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
- What does the "Append Mode" switch do on the Subscription tab?
	- By default, subscriptions will record each downloaded link in its archive file. Append Mode will ignore this file and download everything in the Append List.
	- Append mode will adopt the download location and extra flags of the selected subscription.
	- If you want to perform a one-off download of something specific, it's better to make a list in the "Single" tab and download using that.
- How do I restore a list from the trash?
	- Deleted lists are stored in your `lists/trash` folder.
	- Move the list back to the single or subscriptions folder, then re-create the entry with the "Add List" button. Make sure that the list filename matches, or it won't relink.
- I can't download things from a particular site.
  - This is most likely an issue with gallery-dl. Try updating it from the Config tab, then file an issue on their [GitHub](https://github.com/mikf/gallery-dl) or [Codeberg](https://codeberg.org/mikf/gallery-dl) page if the issue persists.
  - Sometimes, sites may require you to provide cookies, an API key, or for you to log in using OAuth.
- I get a leading zero error after editing the "daterange" option in the config file.
  - Remove any leading zeroes. Instead of using "2026, 01, 01" for January 1st 2026, use "2026, 1, 1" instead. You should only use two digits in the month and day if necessary.