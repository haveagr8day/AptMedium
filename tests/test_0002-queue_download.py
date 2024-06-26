from .shared_test_code import run, init_cwd
from apt_medium.apt_medium import load_medium_state
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
complexpkg = 'wireshark'
bogushostname = 'somethingelse'

# Test queuing package with no dependencies
def test_queue_direct(capsys, monkeypatch, hostname):
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Need to download 1 packages totaling [0-9,]+ bytes", output[0])
        assert re.match("Add to download queue\\?", output[1])
        assert re.match("Queued %s for download" % (simplepkg), output[2])
        state = load_medium_state()
        assert state['download_queue'][hostname] == [simplepkg]

# Test queuing downloads for a different system
def test_queue_indirect(capsys, monkeypatch, hostname):
    with init_cwd() as (retCode, initDir):
        sethostname(bogushostname)
        args = ['install', '--target=%s' % (hostname), simplepkg]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Need to download 1 packages totaling [0-9,]+ bytes", output[0])
        assert re.match("Add to download queue\\?", output[1])
        assert re.match("Queued %s for download" % (simplepkg), output[2])
        state = load_medium_state()
        assert state['download_queue'][hostname] == [simplepkg]
        assert bogushostname not in state['download_queue']
        assert bogushostname not in state['install_queue']
        sethostname(hostname)

# Test show details
def test_queue_show_details(capsys, monkeypatch):
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg]
        monkeypatch.setattr('sys.stdin', StringIO('sn'))
        assert run(args) == 0
        captured = capsys.readouterr()
        assert re.search("The following NEW packages will be installed:\n  %s\n0 upgraded, 1 newly installed" % (simplepkg), captured.out)

# Test print URIs
def test_queue_print_uri(capsys, monkeypatch):
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg]
        monkeypatch.setattr('sys.stdin', StringIO('pn'))
        assert run(args) == 0
        assert re.search("'.*:\\/+.*%s.*\\.deb' %s.*\\.deb [0-9]+" % (simplepkg, simplepkg), captured.out)

# Test queuing package with dependencies
def test_queue_with_deps(capsys, monkeypatch, hostname):
    with init_cwd() as (retCode, initDir):
        args = ['install', complexpkg]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Need to download [0-9]+ packages totaling [0-9,]+ bytes", output[0])
        assert re.match("Add to download queue\\?", output[1])
        assert re.match("Queued %s for download" % complexpkg, output[2])
        state = load_medium_state()
        assert state['download_queue'][hostname] == [complexpkg]

# Test queuing multiple packages
def test_queue_multiple(capsys, monkeypatch, hostname):
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg, complexpkg]
        monkeypatch.setattr('sys.stdin', StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Need to download [0-9]+ packages totaling [0-9,]+ bytes", output[0])
        assert re.match("Add to download queue\\?", output[1])
        assert re.match("Queued %s for download" % simplepkg, output[2])
        assert re.match("Queued %s for download" % complexpkg, output[3])
        state = load_medium_state()
        assert state['download_queue'][hostname] == [simplepkg,complexpkg]
