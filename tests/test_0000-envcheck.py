from apt_medium.apt_medium import check_sysreqs
import os

# Prevent pytest from running if we are not root
if os.geteuid() != 0:
    raise Exception("Tests must be run as root")

def test_sysreqs():
    check_sysreqs()
