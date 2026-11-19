# Changelog

## 0.3 - 2026/11/XX
The user interface gets a complete redesign, along with some changes to how append mode works.

### Update Instructions
- If you already have a copy of batchGDL, ***delete the existing batchGDL folder*** before dropping in the version inside the zip. The structure of the code has changed since the last update. Avoiding this step might cause unintended behavior.
- The readme has been updated. If you have a local copy, consider replacing it.
- Append list behavior has changed. If you still have a "#append.txt" file in your /lists folder, you should delete it.
- _**Do not replace the `batchGDL-config.json` or `gdl-config.json` files as it will destroy your settings!**_

### Added:
- New UI
  - Download jobs are now listed in a tree-style list on the left, as are the search, settings, and add list buttons.
  - The list editor is now always visible on the right side of the screen.
    - This change makes the button to open the list file always visible.
- Append Mode Changes
  - Each subscription job now has its own append list, letting you run multiple append jobs in parallel.

### Fixes:
- Removed excess refresh config buttons from the settings menus.
- On a "Download All" run, the download terminal previously printed "Job Failed" if any errors were raised, despite the download otherwise being successful. To prevent confusion, it will instead print "Job completed with errors. Continuing."
- "Job finished with code [X]" messages have been changed to say "Download finished with errors. (Code [X].)"
- Changing a list filename in-app will rename the file so you don't have to do it manually.

### Changes:
- Lots of UI code has been moved to the widgets folder.

## 0.2.2 - 2026/10/08
I bring some small anti-annoyance changes with this version.
### Fixes:

- The "reset all" option in OAuth settings now requires user input to move onto the next website. This gives you time to read potential OAuth errors.

### Changes:
- Renamed "Edit Downloader Config" to "Edit batchGDL Config"
- Renamed Config tab to "Settings"
- The settings menu has been split into 3 tabs.

## 0.2.1 - 2026/09/22

### Breaking Changes:
- The config file format has been updated. Old config files will be updated upon your next launch of the app.
  - The daterange and cookies_browser options are no longer hardcoded into the downloader. Upon startup, they will be moved to the new global flags string.
  - The single tab will only receive the cookies_browser variable from the config update. 

### Added:
- Global Flags
  - You can now set default command line options for all download jobs within the single tab and subscriptions tab.
- Config Updater
  - If an update changes the config format (like this one, for example), your options will automatically be migrated to the new format.
  - A backup copy of the original config will be made prior to the update.
- You can now check for program updates in the config tab.
- An "Ignore Archive" toggle has been added to the Subscriptions tab. (Can only be enabled when Append Mode is on.)

### Fixes:
- Quotation marks (") will be replaced by apostrophes (') when saving global or list-specific flags.
- The Download All option in the subscription tab now works properly on Linux and MacOS.
- Search now works for single lists.
- Download jobs no longer instantly close the terminal upon completion.
- run_windows.bat now falls back to using cmd if Windows Terminal isn't installed.
- Append mode changed to strip `--filter` from subscription global flags. It functionally works the same as it did in 0.2. You can override this by re-adding it into the job-specific flags, if you wish.

## 0.2 - 2026/08/07

### Breaking Changes:
If you haven't used 0.1, then ignore this section.
- Lists have been moved to two subfolders according to their type:
  - /lists/single
  - /lists/subscriptions

### Added:
- If dependencies are missing, the script will now prompt to install them. 
- List management (add/remove) from within the TUI.
- Custom single lists can now be created.
- Lists are moved to a trash folder instead of being instantly deleted.
- You can now add extra flags for each download job.
- Refresh buttons have been added for situations in which you manually edit the config file.
- A "header" is added before each download run in the log to make it easier to parse and sniff out download errors.

### Fixes:
- Edit list buttons now work on all platforms.
- Fixed log text appearing in the terminal upon editing a .json file.
- Fixed wrapping and spacing issues.

## 0.1
Initial version.
