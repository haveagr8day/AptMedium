"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

    Copyright (c) 2017 Riley Baxter
"""

def getch():
    import sys, tty, termios #@UnresolvedImport Suppress an incorrect PyDev error
    
    # Save original state of stdin
    stdin_fd = sys.stdin.fileno()
    orig_settings = termios.tcgetattr(stdin_fd)
    
    try:
        # Switch to raw mode and read a character
        tty.setraw(stdin_fd)
        ch = sys.stdin.read(1)
    finally:
        # Restore original state of stdin
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, orig_settings)
    
    return ch
