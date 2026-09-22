# Changelog
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

### Fixes:
- Quotation marks (") will be replaced by apostrophes (') when saving global or list-specific flags.
- The Download All option in the subscription tab now works properly on Linux and MacOS.
- The search tab can now search lists in both download tabs, like originally intended.
- Download jobs no longer close the terminal instantly. They will now prompt for user input before closing.
- Pycache is cleared on every launch.

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