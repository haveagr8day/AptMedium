import pytest
import socket

@pytest.fixture
def hostname():
    return socket.gethostname()
