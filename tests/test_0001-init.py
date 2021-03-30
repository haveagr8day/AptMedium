from .shared_test_code import run, init_cwd, init_non_cwd
import os
import pytest
import socket

def verify(initdir):
    os.chdir(initdir)
    hostname = socket.gethostname()
    assert os.path.isdir(os.path.join('archives', 'partial'))
    assert os.path.isdir(os.path.join('lists', 'partial'))
    assert os.path.isfile('medium_state')
    assert os.path.isfile(os.path.join('system_info', hostname, 'dpkg-status'))
    assert os.path.isfile(os.path.join('system_info', hostname, 'etc', 'apt', 'apt.conf'))
    assert os.path.isdir(os.path.join('system_info', hostname, 'etc', 'apt', 'apt.conf.d'))
    assert os.path.isfile(os.path.join('system_info', hostname, 'etc', 'apt', 'apt-medium.conf'))
    assert os.path.isdir(os.path.join('var', 'log', 'apt'))

def test_init_cwd():
    with init_cwd() as (retCode, initdir):
        assert retCode == 0
        verify(initdir)

def test_init_non_cwd():
    with init_non_cwd() as (retCode, initdir):
        assert retCode == 0
        verify(initdir)
