- `daterange` - A date at which the subscription downloader will stop. Anything prior to this date will be skipped. By default, it is set to "YYYY, MM, DD". If the subscription tab sees this default value, it will refuse to start downloading.
  - You have to update this manually between subscription runs. In the future, this will be replaced with a "global flags" setting that can be edited from the UI.
- `config_file` - Path to your gallery-dl config file. (include the file extension)
- `log_file` - Path to your gallery-dl logs file.
- `cookies_browser` - The browser to read cookies from. This defaults to Firefox but accepts pretty much any Chromium-based browser, Firefox-based browser, or safari.
  - This will become a default 'global flag' in the future.
- `dl_folder` - Path to a folder to store your downloaded media. Changing this will not reset the download state of a subscription.
- `setup` - Checks if you've used batchGDL before. This prompts new users to edit the config file on the first launch.
- `oauth-sites` - A comma separated list of sites that require OAuth to download (protected) media.

Download lists are formatted like so:

```
"single-lists" {["list_file", "dest_folder", "optional_flags"],}
"subscriptions": {["list_file", "dest_folder", "archive", "optional_flags"],}
```

- `list_file` - Filename of the job's list file. (no extension)
- `dest_folder` - The job's download subfolder. (located underneath `dl_folder`)
- `archive` - Filename of the job's archive file. (no extension)
- `optional_flags` - A string of additional flags to pass to gallery-dl.

# Template
```
{
  "daterange": "YYYY, MM, DD",
  "config_file": "gdl-config.json",
  "log_file": "logfile_latest.txt",
  "cookies_browser": "firefox",
  "dl_folder": "downloads/",
  "setup": "false",
  "#": "Format: single-lists [list_file, dest_folder, optional_flags]; subscriptions [category, list_file, archive, optional_flags]. Optional flags are one string. Make sure to escape special characters with backslashes.",
  "single-lists": {},
  "subscriptions": {},
  "oauth-sites": [
    ""
  ]
}
```