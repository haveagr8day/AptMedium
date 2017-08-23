

  "apt-medium"   Manages an installation medium,
                 especially writeable ones,
                 for multiple, even disconnected
                 and remote, machines.

1) You mount your apt-medium directory.  (i.e. plug in your USB-disk etc.)

2) If you want to install something on the machine you are loged-in to enter:
   "apt-medium install <package>", and if the necessary packages are already
   on the apt-medium they will get installed right away.
   If you want to have something installed on another machine use
   "apt-medium --machine=<hostname> install <package>"

3) If some Packages are missing on the apt-medium you are told you need to
   execute "apt-medium download". You might want to do this at another machine
   with a (faster) internet connection. You can even download on a machine
   running some other operating system. (with "apt-medium.bat download")

   
After downloading you just run "apt-medium install" on your target machines,
and what you have requested and downloaded for those machines will get installed.

If you want to use a graphical apt-frontend with your apt-medium, for
example aptitude or synaptic, you can do so with "apt-medium --apt-tool=aptitude"
