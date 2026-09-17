- `config_file` - Path to your gallery-dl config file. (include the file extension)
- `log_file` - Path to your gallery-dl logs file.
- `dl_folder` - Path to a folder to store your downloaded media. Changing this will not reset the download state of a subscription.
- `setup` - Checks if you've used batchGDL before. This prompts new users to edit the config file on the first launch.
- `oauth-sites` - A comma separated list of sites that require OAuth to download (protected) media.

Download lists are formatted like so:
```
"download-jobs": {
  "single-lists" {["list_file", "dest_folder", "optional_flags"],},
  "subscriptions": {["list_file", "dest_folder", "archive", "optional_flags"],}
}
```

- `list_file` - Filename of the job's list file. (no extension)
- `dest_folder` - The job's download subfolder. (located underneath `dl_folder`)
- `archive` - Filename of the job's archive file. (no extension)
- `optional_flags` - A string of additional flags to pass to gallery-dl.

# Template
```
{
  ~~"daterange": "YYYY, MM, DD",~~
  "config_file": "gdl-config.json",
  "log_file": "logfile_latest.txt",
  ~~"cookies_browser": "firefox",~~
  "dl_folder": "downloads/",
  "setup": "false",
  ~~"#": "Format: single-lists [list_file, dest_folder, optional_flags]; subscriptions [category, list_file, archive, optional_flags]. Optional flags are one string. Make sure to escape special characters with backslashes.",~~
  ~~"single-lists": {},~~
  ~~"subscriptions": {},~~
  "oauth-sites": [
    ""
  ]
}
```
