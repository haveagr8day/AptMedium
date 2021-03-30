from apt_medium.apt_medium import parse_args, process_args
import os
import pytest
import shutil
import tempfile

def run(args):
    parsed_args = parse_args(args)
    return process_args(parsed_args)

class init_cwd:
    def __init__(self):
        tempdir = None
    def __enter__(self):
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        args = ['init']
        return (run(args), self.tempdir)
    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.tempdir)

class init_non_cwd:
    def __init__(self):
        tempdir = None
        cwd = None
    def __enter__(self):
        self.cwd = tempfile.mkdtemp()
        os.chdir(self.cwd)
        self.tempdir = tempfile.mkdtemp()
        args = ['-m', self.tempdir, 'init']
        return (run(args), self.tempdir)
    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.tempdir)
        shutil.rmtree(self.cwd)
