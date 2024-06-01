# Mega.nz Unlimited Download [works only with a fritzbox router]

CLI implemented in python that allows downloading files from a Mega.nz public link to a target folder (only missing files are downloaded) without quota restriction.
Bypassing the quota is achieved by changing the IP address each time 4500 MB of data is downloaded.

The same CLI could be used with another router. To do that you shall update the callback function ```change_ip_address()``` in the file ```changeipcallback.py``` to change the ip address of your router.

## Clone and Install Dependencies

Clone:

```shell
git clone --recurse-submodules https://github.com/okba-zoueghi/mega-download.git
```

The CLI uses MEGAcmd, therefore mega-cmd shall be available.

For installing MEGAcmd, refer to https://github.com/meganz/MEGAcmd

Tested with MEGAcmd versions: 1.5.1.1 | 1.6.3.1

Tested on Rpi 4 running Debian (MEGAcmd deb files can be found in https://mega.nz/linux/repo/)

Install python dependencies:

```shell
cd mega-download
pip install -r requirements.txt
```

## Usage

```
usage: mega-dl.py [-h] -l LINK -t TARGET_FOLDER [-m MAX_DOWNLOAD_TIME] [-f]

Looks for missing files in target folder and downloads them with changing the IP address before each file download

optional arguments:
  -h, --help            show this help message and exit
  -l LINK, --link LINK  mega public link
  -t TARGET_FOLDER, --target-folder TARGET_FOLDER
                        Target folder to store successfully downloaded files
  -m MAX_DOWNLOAD_TIME, --max-download-time MAX_DOWNLOAD_TIME
                        Max download time for a single file in seconds
  -f, --force-logout    Force mega logout
```

### Example:

The '--link' option can be used one or multiple times to downloads files from several links.
The command will fetch the given links and check for missing files in the target folder and download them.

```shell
mega-dl.py --link '<link1>' --link '<link2>' --link '<link3>' --target-folder '<path to target folder>' --force-logout
```
