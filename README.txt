  "apt-medium"   Manages an installation medium for
                 installing/updating packages on multiple
                 (possibly disconnected and/or remote) systems.

1) You mount your apt-medium directory.  (i.e. plug in your USB-disk etc.)

2) If you want to install something on the machine you are logged-in to enter: "apt-medium install <package>", and if the necessary packages are already on the apt-medium they will get installed right away.
   
   If you want to have something installed on another machine use
   "apt-medium install --target=<hostname> <package>"

3) If some Packages are missing on the apt-medium you are told you asked to add them to the download queue. You can then run "apt-medium download" to download any missing packages. You might want to do this at another machine with a (faster) Internet connection.

4) After downloading you just run "apt-medium install" on your target machines,
and what you have requested and downloaded for those machines will get installed.

This application is in very early development. While the steps detailed above should function, some key functionality is still missing (e.g. updating package lists).
