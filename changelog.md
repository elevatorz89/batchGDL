# Changelog
## 0.2.1 - 2026/09/21
### TODO:
- [x] Global flags options for both single and subscription lists.
- [x] Config Changes
  - [x] Updater
    - [x] Make a config updater that runs upon startup
    - [x] Append a config version variable to the config file
    - [x] Before an update, make a backup of the previous config file
  - [x] Change `"single-lists":` to `"single":`
  - [x] Nest both list types underneath a new `"download-jobs"` category
  - [x] Move the current daterange, cookies, and browser variables to global flags.
- [x] Figure out a "check for updates" button.
- [x] Fix mark_setup_complete()
- [x] See if the default subscription global flags cause an error
- [x] Fix invalid date string
- [x] Test config updater on the template (might crash)
- [x] Rewrite config-help
- [x] Rewrite readme
- [x] Test updater on your own config.
- [x] Fix download all on linux/macos

### Breaking Changes:
- The config file format has been updated. Old config files will be updated upon your next launch of the app.

### Added:
- Global Flags
  - You can now set default command line options for all download jobs within the single tab and subscriptions tab.
- Config Updater
  - If an update changes the config format (like this one, for example), your options will automatically be migrated to the new format.
  - A backup copy of the original config will be made prior to the update.
- You can now check for program updates in the config tab.

### Changes:
- The daterange and cookies_browser options are no longer hardcoded into the downloader. Upon startup, they will be moved to the new global flags string.
  - The single tab will only receive the cookies_browser variable from the config update. 

### Fixes:
- Quotation marks (") will be replaced by apostrophes (') when saving global or list-specific flags.
- The Download All option in the subscription tab now works properly on Linux and MacOS.


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