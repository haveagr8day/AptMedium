from .shared_test_code import run, init_cwd
from apt_medium.apt_medium import load_medium_state
import io
import pytest
import re
import socket

simplepkg = 'fonts-3270'
complexpkg = 'wireshark'

# Test queuing package with no dependencies
def test_queue_direct(capsys, monkeypatch, hostname):
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg]
        monkeypatch.setattr('sys.stdin', io.StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Need to download 1 packages totaling [0-9,]+ bytes", output[0])
        assert re.match("Add to download queue\\?", output[1])
        assert re.match("Queued fonts-3270 for download", output[2])
        state = load_medium_state()
        assert state['download_queue'][hostname] == [simplepkg]

# Test show details
def test_queue_show_details(capsys, monkeypatch):
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg]
        monkeypatch.setattr('sys.stdin', io.StringIO('sn'))
        assert run(args) == 0
        captured = capsys.readouterr()
        assert re.search("The following NEW packages will be installed:\n  fonts-3270\n0 upgraded, 1 newly installed", captured.out)

# Test print URIs
def test_queue_print_uri(capsys, monkeypatch):
    with init_cwd() as (retCode, initDir):
        args = ['install', simplepkg]
        monkeypatch.setattr('sys.stdin', io.StringIO('pn'))
        assert run(args) == 0
        captured = capsys.readouterr()
        assert re.search("'http:\\/\\/.*fonts-3270.*\\.deb' fonts-3270.*\\.deb [0-9]+", captured.out)

# Test queuing package with dependencies
def test_queue_with_deps(capsys, monkeypatch, hostname):
    with init_cwd() as (retCode, initDir):
        args = ['install', complexpkg]
        monkeypatch.setattr('sys.stdin', io.StringIO('y'))
        assert run(args) == 0
        captured = capsys.readouterr()
        output = captured.out.splitlines()
        assert re.match("Need to download [0-9]+ packages totaling [0-9,]+ bytes", output[0])
        assert re.match("Add to download queue\\?", output[1])
        assert re.match("Queued wireshark for download", output[2])
        state = load_medium_state()
        assert state['download_queue'][hostname] == [complexpkg]