# apt-medium
Manages an installation medium for installing/updating packages on multiple (possibly disconnected and/or remote) systems.

This application is in very early development. While the steps detailed below should function, some functionality is still missing (e.g. recovering from certain broken package states).
## Requirements
### Dependencies
- apt-get
- dpkg
- python 2.7.x or 3.x
- python-setuptools (needed to install AptMedium, not required to run)
### Installation Medium
- Must be writable
- Must support Unix file permissions (at runtime only, when moving between systems it is not important that these permissions be maintained/restored)
### Permissions
- All apt-medium commands must be run as root

## General Usage
Note: apt-medium must either be run with your installation medium directory as the working directory or with the '-m' option flag followed by the path to your installation medium directory.

* You mount your apt-medium installation medium directory. (i.e. plug in your USB-disk etc.)

* If not already done, on the system you wish to perform package actions on, run "apt-medium init"

* Depending on how up-to-date the package lists on your target system/installation medium are, you may wish to run "apt-medium update" from a system with internet connectivity at this point

* If you want to install something on the system you are currently on, run "apt-medium install <package> [<package 2>...]". If the necessary packages are already on the installation medium they will get installed right away, otherwise you will be notified of the packages that need to be downloaded.
   
* If you want to have something installed on another system use "apt-medium install --target <hostname> <package> [<package 2>...]", you will be notified whether any packages need to be downloaded.

* If some packages are missing on the installation medium you are asked to add them to the download queue. You can then run "apt-medium download" to download any missing packages. You might want to do this at another system with a (faster) Internet connection.

* After downloading, you just run "apt-medium install" on your target systems and the packages that have been fully downloaded and are marked for installation on that system will get installed.

## Example
To install wireshark on an offline system:
<pre>
Offline System (hostname:offline)              Internet Connected System
apt-medium init
                   ------------------------>
                                               apt-medium update
                                               apt-medium install --target offline wireshark
                                               apt-medium download
                   <------------------------
apt-medium install
</pre>
## Automated Testing Status
[![Build Status](https://github.com/haveagr8day/AptMedium/actions/workflows/apt-medium.yml/badge.svg?branch=master)](https://github.com/haveagr8day/AptMedium/actions/workflows/apt-medium.yml)

## License
apt-medium is released under the [GPL version 2](https://opensource.org/licenses/GPL-2.0) or (at your option) any later version.
