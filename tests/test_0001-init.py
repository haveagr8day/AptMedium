from apt_medium.apt_medium import main
from argparse import Namespace
import os
import pytest
import shutil
import socket
import sys
import tempfile

def verify(dir):
    with pytest.raises(SystemExit) as e:
        main()
    assert e.type == SystemExit
    assert e.value.code == 0
    os.chdir(dir)
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
    tempdir = tempfile.mkdtemp()
    os.chdir(tempdir)
    sys.argv.append('init')
    try:
        verify(tempdir)
    finally:
        shutil.rmtree(tempdir)
        sys.argv.pop()

def test_init_non_cwd():
    cwd = tempfile.mkdtemp()
    os.chdir(cwd)
    tempdir = tempfile.mkdtemp()
    sys.argv.append('-m')
    sys.argv.append(tempdir)
    sys.argv.append('init')
    try:
        verify(tempdir)
    finally:
        shutil.rmtree(tempdir)
        shutil.rmtree(cwd)
        sys.argv.pop()
        sys.argv.pop()
        sys.argv.pop()
