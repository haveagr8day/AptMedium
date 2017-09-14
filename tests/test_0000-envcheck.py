from apt_medium.apt_medium import check_sysreqs
import os

def test_sysreqs():
    if os.geteuid() != 0:
        raise Exception("Tests must be run as root")
    check_sysreqs()
