# Mega.nz Unlimited Download

CLI implemented in python that allows downloading files from a Mega.nz public link to a target folder (only missing files are downloaded) without quota restriction.
Bypassing the quota is achieved by changing the IP address each time 4500 MB of data is downloaded.

Download of files of size greater than 5GB is also supported.

The following router families are supported:
- Fritzbox
- Glinet

Using a free mega account can be frustrating since the download is limited to 5GB. A pro mega account allows to download more data but it requires a monthly subscription and also is limited. Since I download too often files from mega, I created this repo to bypass restrictions of free accounts. I made the repo public since this might be useful for other people.

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

### Limitations

Download of large files (> 5GB) is currently only supported from folder links (not supported for single file links)

No parallel download is supported i.e. only one instance of the scripts can run at once. This due to the underlying MEGAcmd commands (e.g. ```mega-login```). For example, a login to a public folder link is necessary to download from a public link and only one login session is possible at the same time.

In case you use a fritzbox, it might be the case that you ip doesn't change, this depends on the your ISP.

In case you use a Glinet router, a VPN subscription is required (tested only with Mullvad).


### Want to Contribute?

You're welcome to create a pull request :)

### Like the repo and want to say thanks?
This repo is developed totally in my free time. If you like it and want to say thanks, you can support me through [!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/okba.zoueghi) or https://www.paypal.com/paypalme/okbazoueghi.
