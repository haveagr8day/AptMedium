from .shared_test_code import init_cwd, init_non_cwd
from apt_medium.apt_medium import load_medium_state
import os
import pytest
import socket

def verify(initDir):
    os.chdir(initDir)
    hostname = socket.gethostname()
    assert os.path.isdir(os.path.join('archives', 'partial'))
    assert os.path.isdir(os.path.join('lists', 'partial'))
    assert os.path.isfile('medium_state')
    assert os.path.isfile(os.path.join('system_info', hostname, 'dpkg-status'))
    assert os.path.isfile(os.path.join('system_info', hostname, 'etc', 'apt', 'apt.conf'))
    assert os.path.isdir(os.path.join('system_info', hostname, 'etc', 'apt', 'apt.conf.d'))
    assert os.path.isfile(os.path.join('system_info', hostname, 'etc', 'apt', 'apt-medium.conf'))
    assert os.path.isdir(os.path.join('var', 'log', 'apt'))
    state = load_medium_state()
    assert 'download_queue' in state
    assert 'install_queue' in state
    assert hostname in state['download_queue']
    assert hostname in state['install_queue']
    assert state['download_queue'][hostname] == []
    assert state['install_queue'][hostname] == []

def test_init_cwd():
    with init_cwd() as (retCode, initDir):
        assert retCode == 0
        verify(initDir)

def test_init_non_cwd():
    with init_non_cwd() as (retCode, initDir):
        assert retCode == 0
        verify(initDir)
