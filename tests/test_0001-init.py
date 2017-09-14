from apt_medium.apt_medium import parse_args, process_args
from argparse import Namespace
import os
import pytest
import shutil
import socket
import sys
import tempfile

def verify(dir,in_args):
    parsed_args = parse_args(in_args)
    retCode = process_args(parsed_args)
    assert retCode == 0
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
    args = ['init']
    try:
        verify(tempdir, args)
    finally:
        shutil.rmtree(tempdir)

def test_init_non_cwd():
    cwd = tempfile.mkdtemp()
    os.chdir(cwd)
    tempdir = tempfile.mkdtemp()
    args = ['-m', tempdir, 'init']
    try:
        verify(tempdir, args)
    finally:
        shutil.rmtree(tempdir)
        shutil.rmtree(cwd)
