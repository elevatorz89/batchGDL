# Config Help

- `config_file` - Path to your gallery-dl config file. (include the file extension)
- `log_file` - Path to your gallery-dl logs file.
- `dl_folder` - Path to a folder to store your downloaded media. Changing this will not reset the download state of a subscription.
- `setup` - Checks if you've used batchGDL before. This prompts new users to edit the config file on the first launch.
- `oauth-sites` - A comma separated list of sites that require OAuth to download (protected) media.
- `download-jobs`
  - `single-lists` - A list of your singles tab download jobs and their config.
  - `subscriptions` - A list of your subscription tab download jobs and their config.
- `global-flags-single` - Extra flags applied to every download job in the singles tab.
- `global-flags-subscriptions` - Extra flags applied to every download job in the subscription tab.
- `config_ver` - The version of the config file format. (Don't modify this.)

Download lists are formatted like so:
```
"download-jobs": {
  "single-lists" {["list_file", "dest_folder", "optional_flags"],}
  "subscriptions": {["list_file", "dest_folder", "archive", "optional_flags"],}
}
```

- `list_file` - Filename of the job's list file. (no extension)
- `dest_folder` - The job's download subfolder. (located underneath `dl_folder`)
- `archive` - Filename of the job's archive file. (no extension)
- `optional_flags` - Extra flags to use for this download job.

# Template (v2)
```
{
  "config_file": "gdl-config.json",
  "log_file": "logfile_latest.txt",
  "dl_folder": "downloads/",
  "setup": "true",
  "oauth-sites": [
    ""
  ],
  "download-jobs": {
    "single": {},
    "subscription": {}
  },
  "global-flags-single": [
    "--cookies-from-browser firefox"
  ],
  "global-flags-subscriptions": [
    "--filter 'date >= datetime(1970, 1, 1) or abort()' --cookies-from-browser firefox"
  ],
  "config_ver": 2
}
```
> Note that the format of the date filter is `datetime(YYYY, MM, DD)`.