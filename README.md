# Mega.nz Unlimited Download [works only with a fritzbox router]

CLI implemented in python that files from a Mega.nz public link to a target folder (only missing files are downloaded) without quoata restriction.
Bypassing the quota is achieved by changing the IP address of the fritzbox before each file download.

The same CLI could be used with another router in case a function for changing the ip for the router is available (needs to be adapted).

## Usage

```shell
usage: mega-dl.py [-h] [-l LINK] [-t TARGET_FOLDER]

Looks for missing files in target folder and downloads them with changing the IP address before each file download

optional arguments:
  -h, --help            show this help message and exit
  -l LINK, --link LINK
  -t TARGET_FOLDER, --target-folder TARGET_FOLDER
```

### Example:

The '--link' option can be used multiple times to downloads files from several links.
The command will fetch the given links and check for missing files in the target folder and download them.

```shell
mega-dl.py --link '<link1>' --link '<link2>' --link '<link3>' --target-folder '<path to target folder>' 
```
