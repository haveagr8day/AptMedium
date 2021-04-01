from .shared_test_code import run, init_cwd
from apt_medium.apt_medium import load_medium_state
import glob
import pytest
import os
import re
import socket

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from socket import sethostname
except ImportError:
    def sethostname(hostname):
        os.system("hostname %s" % (hostname))
        assert socket.gethostname() == hostname

simplepkg = 'fonts-3270'
simplepkg2 = 'fonts-adf-accanthis'
complexpkg = 'tshark'
complexdep = 'libwireshark'
bogushostname = 'somethingelse'

# Test downloading package with no dependencies
def test_download(capsys, monkeypatch, hostname):
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        capsys.readouterr()
        args = ['download']
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Pending download actions:", output[0])
        assert re.match("\t%s:" % (hostname), output[1])
        assert re.match("\t\tinstall %s" % (simplepkg), output[2])
        assert re.match("About to download 1 packages totaling [0-9,]+ bytes", output[3])
        assert re.match("Continue with download\\?", output[4])
        assert re.match("Download completed successfully", output[-1])
        state = load_medium_state()
        assert state['download_queue'][hostname] == []
        assert state['install_queue'][hostname] == [simplepkg]
        assert glob.glob('archives/' + simplepkg + "*.deb")

# Test downloading package with dependencies
def test_download_deps(capsys, monkeypatch, hostname):
    with init_cwd() as (retcode, initDir):
        args = ['install', complexpkg]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        capsys.readouterr()
        args = ['download']
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Pending download actions:", output[0])
        assert re.match("\t%s:" % (hostname), output[1])
        assert re.match("\t\tinstall %s" % (complexpkg), output[2])
        assert re.match("About to download [0-9]+ packages totaling [0-9,]+ bytes", output[3])
        assert re.match("Continue with download\\?", output[4])
        assert re.match("Download completed successfully", output[-1])
        state = load_medium_state()
        assert state['download_queue'][hostname] == []
        assert state['install_queue'][hostname] == [complexpkg]
        assert glob.glob('archives/' + complexpkg + "*.deb")
        assert glob.glob('archives/' + complexdep + "*.deb")

# Test downloading multiple packages
def test_download_multiple_pkg(capsys, monkeypatch, hostname):
    with init_cwd() as (retcode, initDir):
        args = ['install', simplepkg, simplepkg2]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        capsys.readouterr()
        args = ['download']
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Pending download actions:", output[0])
        assert re.match("\t%s:" % (hostname), output[1])
        assert re.match("\t\tinstall %s, %s" % (simplepkg, simplepkg2), output[2])
        assert re.match("About to download [0-9]+ packages totaling [0-9,]+ bytes", output[3])
        assert re.match("Continue with download\\?", output[4])
        assert re.match("Download completed successfully", output[-1])
        state = load_medium_state()
        assert state['download_queue'][hostname] == []
        assert state['install_queue'][hostname] == [simplepkg,simplepkg2]
        assert glob.glob('archives/' + simplepkg + "*.deb")
        assert glob.glob('archives/' + simplepkg2 + "*.deb")

# Test downloading packages for a specific system
def test_download_target(capsys, monkeypatch, hostname):
    sethostname(bogushostname)
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        sethostname(hostname)
        args = ['init']
        assert run(args) == 0
        args = ['install', simplepkg2]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        capsys.readouterr()
        args = ['download', '-t', bogushostname]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Pending download actions:", output[0])
        assert re.match("\t%s:" % (bogushostname), output[1])
        assert re.match("\t\tinstall %s" % (simplepkg), output[2])
        assert re.match("About to download 1 packages totaling [0-9,]+ bytes", output[3])
        assert re.match("Continue with download\\?", output[4])
        assert re.match("Download completed successfully", output[-1])
        state = load_medium_state()
        assert state['download_queue'][bogushostname] == []
        assert state['install_queue'][bogushostname] == [simplepkg]
        assert state['download_queue'][hostname] == [simplepkg2]
        assert state['install_queue'][hostname] == []
        assert glob.glob('archives/' + simplepkg + "*.deb")
        assert not glob.glob('archives/' + simplepkg2 + "*.deb")

# Test downloading packages for multiple systems
def test_download_multiple_sys(capsys, monkeypatch, hostname):
    sethostname(bogushostname)
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        sethostname(hostname)
        args = ['init']
        assert run(args) == 0
        args = ['install', simplepkg2]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        capsys.readouterr()
        args = ['download']
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Pending download actions:", output[0])
        assert re.match("Download completed successfully", output[-1])
        state = load_medium_state()
        assert state['download_queue'][bogushostname] == []
        assert state['install_queue'][bogushostname] == [simplepkg]
        assert state['download_queue'][hostname] == []
        assert state['install_queue'][hostname] == [simplepkg2]
        assert glob.glob('archives/' + simplepkg + "*.deb")
        assert glob.glob('archives/' + simplepkg2 + "*.deb")
