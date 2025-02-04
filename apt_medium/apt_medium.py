#!/usr/bin/env python
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

    Based on a proof-of-concept written by Christian Gatzemeier (Copyright (c) 2007)  
    Copyright (c) 2018 Riley Baxter
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile

from .utils import getch, native_to_unicode

try:
    import cPickle as pickle
except ImportError as _:
    import pickle

try:
    from distutils.spawn import find_executable as find_exe
except ImportError as _:
    from shutil import which as find_exe

tempfiles = []

def main():
    # Replace sys.argv[0] with absolute path to allow easy reinvokation even if cwd has changed
    sys.argv[0] = os.path.abspath(sys.argv[0])
    
    try:
        args = parse_args(sys.argv[1:])
    except Exception as e:
        print(e)
        return 1
    
    try:
        check_sysreqs()
    except Exception as e:
        print(e)
        return 1
   
    return process_args(args)
 
def parse_args(in_args):
    main_parser = argparse.ArgumentParser(description='Manages an installation medium for installing/updating packages on multiple (possibly disconnected and/or remote) systems.')
    sub_parsers = main_parser.add_subparsers(dest='action', metavar='action')
    sub_parsers.required = True
    
    main_parser.add_argument('-m', '--install-medium', type=native_to_unicode, default=os.getcwd(), help='path to installation medium (defaults to current working directory)')
    
    # Create a parser for the init command
    sub_parsers.add_parser('init', help='initialize or update the dpkg status and apt configuration for this system in the installation medium')
    
    # Create a parser for the update command
    update_parser = sub_parsers.add_parser('update', help='retrieve new lists of packages (network connectivity required)')
    update_parser.add_argument('-t', '--target', metavar='hostname', type=native_to_unicode, help='the hostname of the system to update package lists for (default is all systems)')
    
    # Create a parser for the upgrade command
    upgrade_parser = sub_parsers.add_parser('upgrade', help='update all currently installed packages to latest versions (based on current package lists, may need to use "update" first to achieve desired effect)')
    upgrade_parser.add_argument('--force', action='store_true', help='force apt-get to proceed (--force-yes) even if a dangerous situation is detected')
    upgrade_parser.add_argument('-f', '--fix-broken', action='store_true', help='Tell apt-get to attempt to resolve broken dependencies (not fully implemented yet, must manually copy resulting package list)')
    upgrade_parser.add_argument('-t', '--target', metavar='hostname', type=native_to_unicode, default=socket.gethostname(), help='the hostname of the target system to perform the upgrades on (defaults to the current system)')
  
    # Create a parser for the dist-upgrade command
    dist_upgrade_parser = sub_parsers.add_parser('dist-upgrade', help='update all currently installed packages (including adding or removing packages as needed to resolve dependencies) (based on current package lists, may need to use "update" first to achieve desired effect)')
    dist_upgrade_parser.add_argument('--force', action='store_true', help='force apt-get to proceed (--force-yes) even if a dangerous situation is detected')
    dist_upgrade_parser.add_argument('-f', '--fix-broken', action='store_true', help='Tell apt-get to attempt to resolve broken dependencies (not fully implemented yet, must manually copy resulting package list)')
    dist_upgrade_parser.add_argument('-t', '--target', metavar='hostname', type=native_to_unicode, default=socket.gethostname(), help='the hostname of the target system to perform the upgrades on (defaults to the current system)')
    
    # Create a parser for the install command
    install_parser = sub_parsers.add_parser('install', help='install or upgrade a package (or queue the action if downloads are needed)')
    install_parser.add_argument('-t', '--target', metavar='hostname', type=native_to_unicode, default=socket.gethostname(), help='the hostname of the target system to perform the install/upgrade on (defaults to the current system)')
    install_parser.add_argument('--force', action='store_true', help='force apt-get to proceed (--force-yes) even if a dangerous situation is detected')
    install_parser.add_argument('-f', '--fix-broken', action='store_true', help='Tell apt-get to attempt to resolve broken dependencies (not fully implemented yet, must manually copy resulting package list)')
    install_parser.add_argument('packages', type=native_to_unicode, nargs='*', help='package name(s) to be installed')
    
    # Create a parser for the download command
    download_parser = sub_parsers.add_parser('download', help='download files/packages needed to complete pending actions (network connectivity required)')
    download_parser.add_argument('-t', '--target', metavar='hostname', type=native_to_unicode, help='the hostname of the system to complete pending downloads for (default is all systems)')
    download_parser.add_argument('--force', action='store_true', help='force apt-get to proceed (--force-yes) even if a dangerous situation is detected')
    download_parser.add_argument('--allow-unauthenticated', action='store_true', help='tell apt-get to proceed even if downloads cannot be authenticated')
    
    # TODO: Create a parser for the show-queue command
    
    # TODO: Create a parser for the clear-queue command 
    
    args = main_parser.parse_args(in_args)
    args.action = native_to_unicode(args.action)
    args.install_medium = os.path.abspath(args.install_medium)
    
    if os.path.isdir(args.install_medium):
        os.chdir(args.install_medium)
    else:
        raise Exception('The specified installation medium (' + args.install_medium + ') does not exist.')
    
    try:
        f = open('testfile','w')
        f.write('test')
        f.close()
        os.unlink('testfile')
    except (IOError,OSError) as _:
        raise Exception('The specified installation medium (' + args.install_medium + ') does not appear to be writeable, read-only install mediums are not currently supported')
    
    return args

def process_args(args):
    if args.action == 'init':
        retCode = init_action()
    elif args.action == 'update':
        retCode = update_action(args)
    elif args.action == 'upgrade':
        retCode = upgrade_action(args, isDistUpgrade=False)
    elif args.action == 'dist-upgrade':
        retCode = upgrade_action(args, isDistUpgrade=True)
    elif args.action == 'install':
        retCode = install_action(args)
    elif args.action == 'download':
        retCode = download_action(args)
    
    # Cleanup temporary files
    for f in tempfiles:
        f.close()
    
    return retCode

def check_sysreqs():
    # Check if we are running as root
    if os.geteuid() != 0:
        # If not, restart ourselves as root
        #if find_exe('sudo'):
        #    os.execvp("sudo", ["sudo"] + sys.argv)
        #else:
        raise Exception('apt-medium must be run as root.')
    
    if not find_exe('apt-get'):
        raise Exception('Cannot find apt-get in PATH.')
    
    if not find_exe('dpkg'):
        raise Exception('Cannot find dpkg in PATH.')

def sync_local_lists():
    medium_lists_dir = 'lists'
    local_lists_dir = '/var/lib/apt/lists'
    for f in os.listdir(local_lists_dir):
        src_file = os.path.join(local_lists_dir, f)
        dst_file = os.path.join(medium_lists_dir, f)
        
        if f == 'lock' or not os.path.isfile(src_file):
            continue
        
        if not os.path.exists(dst_file) or os.path.getmtime(src_file) > os.path.getmtime(dst_file):
            shutil.copy(src_file,dst_file)
    
def load_medium_state():
    if not os.path.isfile('medium_state'):
        print('medium_state file not found on the installation medium (' + os.getcwd() + ')')
        print('Check you have specified the correct medium and that at least one system has been initialized on the medium')
        exit(-1)
    state_file = open('medium_state', 'rb')
    state = pickle.load(state_file)
    state_file.close()
    return state

def save_medium_state(state):
    state_file = open('medium_state', 'wb')
    pickle.dump(state, state_file, protocol=2)
    state_file.close()
    
def validate_queues():
    raise NotImplementedError()

def setup_config_redirect(env, config_location):
    redir_conf = tempfile.NamedTemporaryFile(mode='w')
    tempfiles.append(redir_conf)
    redir_conf.write('Dir::Etc "' + config_location + '";')
    env['APT_CONFIG'] = redir_conf.name
    return env

def init_action():
    hostname = socket.gethostname()
    
    info_dir = 'system_info'
    system_dir = os.path.join(info_dir, hostname)
    system_etc_dir = os.path.join(system_dir, 'etc')
    
    lists_dir = 'lists'
    lists_partial_dir = os.path.join(lists_dir, 'partial')
    
    archives_dir = 'archives'
    archives_partial_dir = os.path.join(archives_dir, 'partial')
    
    var_dir = 'var'
    var_log_dir = os.path.join(var_dir, 'log')
    var_log_apt_dir = os.path.join(var_log_dir, 'apt')
    
    # Create directory structure
    for directory in [info_dir, system_dir, system_etc_dir,
                      lists_dir, lists_partial_dir, archives_dir,
                      archives_partial_dir, var_dir, var_log_dir, var_log_apt_dir]:
        if not os.path.exists(directory):
            os.mkdir(directory)
    
    if not os.path.exists('medium_state'):
        state = {}
        state['install_queue'] = {}
        state['download_queue'] = {}
        save_medium_state(state)
    
    # Copy necessary information about the system
    system_apt_dir = os.path.join(system_etc_dir, 'apt')
    shutil.copy('/var/lib/dpkg/status', os.path.join(system_dir, 'dpkg-status'))
    if os.path.exists(system_apt_dir):
        shutil.rmtree(system_apt_dir)
    shutil.copytree('/etc/apt', system_apt_dir)
    
    # Create an empty apt.conf.d folder if one doesn't exist
    apt_conf_d_dir = os.path.join(system_apt_dir, 'apt.conf.d')
    if not os.path.exists(apt_conf_d_dir):
        os.mkdir(apt_conf_d_dir)
    
    # Create an empty apt.conf file if one doesn't exist
    apt_conf = os.path.join(system_apt_dir, 'apt.conf')
    open(apt_conf, 'a').close()
    
    # Create a base configuration that loads apt.conf.d and apt.conf
    apt_medium_conf = os.path.join(system_apt_dir, 'apt-medium.conf')
    am_conf = open(apt_medium_conf, 'w')
    
    am_conf.write('APT\n')
    am_conf.write('    {\n')
    am_conf.write('    Architecture "' + subprocess.check_output(['dpkg', '--print-architecture']).splitlines()[0].decode('utf-8') + '";\n');
    foreign_archs = subprocess.check_output(['dpkg', '--print-foreign-architectures']).decode('utf-8').splitlines()
    if len(foreign_archs) > 0:
        am_conf.write('    Architectures {')
        for arch in foreign_archs:
            am_conf.write('"' + arch + '";')
        am_conf.write('};\n')
    # keep all lists (i.e. those not in current sources.list file) on apt-medium for use by offline machines
    am_conf.write('    Get::List-Cleanup "false";\n')
    am_conf.write('    };\n')
    
    am_conf.write('Dir\n')
    am_conf.write('    {\n')
    am_conf.write('    State "./' + system_dir + '";\n')
    am_conf.write('    State::status "dpkg-status";\n')
    am_conf.write('    State::Lists "./' + lists_dir + '";\n')
    am_conf.write('    Cache "./' + system_dir + '";\n')
    am_conf.write('    Cache::archives "./' + archives_dir + '";\n')
    am_conf.write('    Etc "./' + system_apt_dir + '";\n')
    am_conf.write('    };\n')
    
    am_conf.close()
    
    sync_local_lists()
    
    state = load_medium_state()
    if hostname not in state['install_queue']:
        state['install_queue'][hostname] = []
        state['download_queue'][hostname] = []
        save_medium_state(state)
    
    return 0

def update_action(args):
    install_medium = args.install_medium
    target = args.target
    
    state = load_medium_state()
    if target:
        all_systems = False
        if not os.path.exists(os.path.join(install_medium, 'system_info', target)):
            print('Cannot find target (' + target + ') on medium (' + install_medium + ') check that your spelling is correct and that the target has been initialized on the medium')
            return -1
    else:
        all_systems = True
    
    success = True
    for system in (state['download_queue'] if all_systems else [target]):
        target_info_dir = os.path.join(install_medium, 'system_info', system)
        target_apt_dir = os.path.join(target_info_dir, 'etc', 'apt')
        # Prepare configuration file to redirect location of /etc/apt in apt-get
        env = setup_config_redirect(os.environ, target_apt_dir)
        
        parms = ['apt-get']
        
        # Set RootDir to installation medium location
        parms.append('--option')
        parms.append('Dir=' + install_medium)
        
        # Load target's apt-medium.conf file
        parms.append('--config-file')
        parms.append(os.path.join(target_apt_dir, 'apt-medium.conf'))
        
        parms.append('update')
        
        proc = subprocess.Popen(parms, env=env)
        
        if proc.wait() != 0:
            print('\napt-get failed while updating package lists for target: ' +  system)
            success = False
    
    if success:
        # Note that apt-get returns an exit code of 0 on download failures.
        # TODO: Try to find a better way to handle this.
        print('\nPackage list updating complete\nCheck the above output for any download warnings/errors')
    else:
        print('\nOne or more package list update actions failed')

def upgrade_action(args, isDistUpgrade):
    target = args.target
    install_medium = args.install_medium
    force = args.force
    fix_broken = args.fix_broken
    
    local_is_target = target == socket.gethostname()
    
    target_info_dir = os.path.join(install_medium, 'system_info', target)
    target_apt_dir = os.path.join(target_info_dir, 'etc', 'apt')
    
    state = load_medium_state()
    
    # Verify upgrade target has been initialized
    if not os.path.exists(target_info_dir) or target not in state['install_queue']:
        print('Cannot find target (' + target + ') on medium (' + install_medium + ') check that your spelling is correct and that the target has been initialized on the medium')
        return -1
    
    # If target is initialized and target is this system, reinitialize to ensure we are up to date
    if local_is_target:
        init_action()
    
    # Prepare configuration file to redirect location of /etc/apt in apt-get
    env = setup_config_redirect(os.environ, target_apt_dir)
    
    parms = ['apt-get']
    
    # Set RootDir to installation medium location
    parms.append('--option')
    parms.append('Dir=' + install_medium)
    
    # Load target's apt-medium.conf file 
    parms.append('--config-file')
    parms.append(os.path.join(target_apt_dir, 'apt-medium.conf'))

    if isDistUpgrade:
        parms.append('dist-upgrade')
    else:
        parms.append('upgrade')
    
    if fix_broken:
        parms.append('--fix-broken')
    
    if force:
        parms.append('--force-yes')
    else:
        parms.append('--assume-yes')
    
    # Check if all needed downloads are present
    try:
        check_parms = list(parms)
        check_parms.append('--print-uris')
        check_parms.append('-qq')
        uris = subprocess.check_output(check_parms, env=env).decode('utf-8').splitlines()
    except subprocess.CalledProcessError as _:
        print('apt-get failed while checking for needed packages')
        return -1
    
    total_size = 0
    num_missing = 0
    for item in uris:
        item = item.split()
        if item == []: continue
        if len(item) != 4: continue
        if not item[0].startswith("'http"): continue
        total_size += int(item[2])
        num_missing += 1

    if num_missing > 0:
        print('Need to download ' + str(num_missing) + ' packages totaling ' + '{:,}'.format(total_size) + ' bytes')
        while True:
            print('Add to download queue? Yes (y), No(n), or Show Details (s) or Print URIs (p):', end='')
            sys.stdout.flush()
            response = getch()
            print(response)
            response = response.lower()
            if response == 'y' or response == 'n':
                break
            elif response == 's':
                print()
                detail_parms = list(parms)
                detail_parms.append('--simulate')
                detail_output = subprocess.check_output(detail_parms, env=env).decode('utf-8').splitlines()
                for line in detail_output:
                    if re.search('Reading package lists', line) or re.search('Building dependency tree', line) or re.search('Reading state information', line):
                        continue
                    print(line)
                    if re.search(r'[0-9]* newly installed', line):
                        break
                print()
            elif response == 'p':
                print()
                for item in uris:
                    print(item)
                print()
            else:
                print('Invalid selection.')
        if response == 'y':
            state = load_medium_state()
            
            # Parse packages to be upgraded from details and queue as a standard download for installation
            detail_parms = list(parms)
            detail_parms.append('--simulate')
            detail_output = subprocess.check_output(detail_parms, env=env).decode('utf-8').splitlines()
            
            get_pkgs = False
            packages = []
            for line in detail_output:
                if re.search('NEW packages will be installed', line) or re.search('packages will be upgraded', line):
                    get_pkgs = True
                    continue
                if re.search('packages will be REMOVED', line) or re.search('have been kept back', line):
                    get_pkgs = False
                    continue
                if re.search(r'[0-9]* newly installed', line):
                    break
                if get_pkgs:
                    for pkg in line.split():
                        packages.append(pkg)
            
            for package in packages:
                if package not in state['download_queue'][target]:
                    state['download_queue'][target].append(package)
                    print('Queued ' + package + ' for download')
                else:
                    print(package + ' already queued for download')
            save_medium_state(state)
        else: # response == 'n'
            pass
    else:
        detail_parms = list(parms)
        detail_parms.append('--simulate')
        detail_output = subprocess.check_output(detail_parms, env=env).decode('utf-8').splitlines()
        at_sim_details = False
        nothing_to_do = True
        get_pkgs = False
        packages = []
        for line in detail_output:
            if not at_sim_details:
                if re.search('NEW packages will be installed', line) or re.search('packages will be upgraded', line):
                    get_pkgs = True
                    continue
                if re.search('packages will be REMOVED', line) or re.search('have been kept back', line):
                    get_pkgs = False
                    continue
                if re.search('is already the newest version', line):
                    print(line)
                if re.search(r'[0-9]* newly installed', line):
                    at_sim_details = True
                    continue
                if get_pkgs:
                    for pkg in line.split():
                        packages.append(pkg)
            else:
                nothing_to_do = False
                break
        if not nothing_to_do:
            if not local_is_target:
                print('Ready to upgrade ' + ", ".join(packages) + ' on ' + target)
                while True:
                    print('Add to install queue? Yes (y), No(n), or Show Details (s):', end='')
                    sys.stdout.flush()
                    response = getch()
                    print(response)
                    response = response.lower()
                    if response == 'y' or response == 'n':
                        break
                    elif response == 's':
                        print()
                        for line in detail_output:
                            if re.search('Reading package lists', line) or re.search('Building dependency tree', line) or re.search('Reading state information', line):
                                continue
                            print(line)
                            if re.search(r'[0-9]* newly installed', line):
                                break
                        print()
                    else:
                        print('Invalid selection.')
                if response == 'y':
                    state = load_medium_state()
                    for package in packages:
                        if package not in state['install_queue'][target]:
                            state['install_queue'][target].append(package)
                            print('Queued ' + package + ' for install')
                        else:
                            print(package + ' already queued for install')
                    save_medium_state(state)
                else: # response == 'n'
                    pass
            else:
                print('Ready to upgrade ' + ", ".join(packages))
                while True:
                    print('Continue with upgrade? Yes (y), No(n), or Show Details (s):', end='')
                    sys.stdout.flush()
                    response = getch()
                    print(response)
                    response = response.lower()
                    if response == 'y' or response == 'n':
                        break
                    elif response == 's':
                        print()
                        for line in detail_output:
                            if re.search('Reading package lists', line) or re.search('Building dependency tree', line) or re.search('Reading state information', line):
                                continue
                            print(line)
                            if re.search(r'[0-9]* newly installed', line):
                                break
                        print()
                    else:
                        print('Invalid selection.')
                if response == 'y':
                    # Override archives parameter with absolute path since apt-get refuses to install from a relative path
                    parms.append('--option')
                    parms.append('Dir::Cache::archives=' + os.path.join(install_medium, 'archives'))
                    proc = subprocess.Popen(parms, env=env)
                    
                    if proc.wait() != 0:
                        print('apt-get failed while installing packages')
                        return -1
                    
                    print ('Installation successful')
                    state = load_medium_state()
                    for package in packages:
                        if package in state['install_queue'][target]:
                            state['install_queue'][target].remove(package)
                    save_medium_state(state)
                    
                    # Re-sync dpkg status info
                    init_action()
                else: # response == 'n'
                    pass
        else:
            state = load_medium_state()
            for package in packages:
                if package in state['install_queue'][target]:
                    state['install_queue'][target].remove(package)
            save_medium_state(state)
            print('All packages already installed/up-to-date')
    
    return 0
    
def install_action(args):
    target = args.target
    install_medium = args.install_medium
    packages = args.packages
    force = args.force
    fix_broken = args.fix_broken
    local_is_target = target == socket.gethostname()
    
    target_info_dir = os.path.join(install_medium, 'system_info', target)
    target_apt_dir = os.path.join(target_info_dir, 'etc', 'apt')
    
    state = load_medium_state()
    # Verify install target has been initialized
    if not os.path.exists(target_info_dir) or target not in state['install_queue']:
        print('Cannot find target (' + target + ') on medium (' + install_medium + ') check that your spelling is correct and that the target has been initialized on the medium')
        return -1
    
    # If target is initialized and target is this system, reinitialize to ensure we are up to date
    if local_is_target:
        init_action()
    
    # Prepare configuration file to redirect location of /etc/apt in apt-get
    env = setup_config_redirect(os.environ, target_apt_dir)
    
    parms = ['apt-get']
    
    # Set RootDir to installation medium location
    parms.append('--option')
    parms.append('Dir=' + install_medium)
    
    # Load target's apt-medium.conf file 
    parms.append('--config-file')
    parms.append(os.path.join(target_apt_dir, 'apt-medium.conf'))
    
    parms.append('install')
    
    if fix_broken:
        parms.append('--fix-broken')
    
        if packages:
            parms.extend(packages)
    else:
        if packages:
            parms.extend(packages)
        else:
            state = load_medium_state()
            if len(state['install_queue'][target]) > 0:
                packages = state['install_queue'][target]
                parms.extend(packages)
            else:
                print('Nothing to install')
                return 0
    
    if force:
        parms.append('--force-yes')
    else:
        parms.append('--assume-yes')
    
    # Check if all needed downloads are present
    try:
        check_parms = list(parms)
        check_parms.append('--print-uris')
        check_parms.append('-qq')
        uris = subprocess.check_output(check_parms, env=env).decode('utf-8').splitlines()
    except subprocess.CalledProcessError as _:
        print('apt-get failed while checking for needed packages')
        return -1
    
    total_size = 0
    num_missing = 0
    for item in uris:
        item = item.split()
        if item == []: continue
        total_size += int(item[2])
        num_missing += 1
    
    if num_missing > 0:
        print('Need to download ' + str(num_missing) + ' packages totaling ' + '{:,}'.format(total_size) + ' bytes')
        while True:
            print('Add to download queue? Yes (y), No(n), or Show Details (s) or Print URIs (p):', end='')
            sys.stdout.flush()
            response = getch()
            print(response)
            response = response.lower()
            if response == 'y' or response == 'n':
                break
            elif response == 's':
                print()
                detail_parms = list(parms)
                detail_parms.append('--simulate')
                detail_output = subprocess.check_output(detail_parms, env=env).decode('utf-8').splitlines()
                for line in detail_output:
                    if re.search('Reading package lists', line) or re.search('Building dependency tree', line) or re.search('Reading state information', line):
                        continue
                    print(line)
                    if re.search(r'[0-9]* newly installed', line):
                        break
                print()
            elif response == 'p':
                print()
                for item in uris:
                    print(item)
                print()
            else:
                print('Invalid selection.')
        if response == 'y':
            state = load_medium_state()
            for package in packages:
                if package not in state['download_queue'][target]:
                    state['download_queue'][target].append(package)
                    print('Queued ' + package + ' for download')
                else:
                    print(package + ' already queued for download')
            save_medium_state(state)
        else: # response == 'n'
            pass
    else:
        detail_parms = list(parms)
        detail_parms.append('--simulate')
        detail_output = subprocess.check_output(detail_parms, env=env).decode('utf-8').splitlines()
        at_sim_details = False
        nothing_to_do = True
        for line in detail_output:
            if not at_sim_details:
                if re.search('is already the newest version', line):
                    print(line)
                if re.search(r'[0-9]* newly installed', line):
                    at_sim_details = True
            else:
                nothing_to_do = False
                break
        if not nothing_to_do:
            if not local_is_target:
                print('Ready to install ' + ", ".join(packages) + ' on ' + target)
                while True:
                    print('Add to install queue? Yes (y), No(n), or Show Details (s):', end='')
                    sys.stdout.flush()
                    response = getch()
                    print(response)
                    response = response.lower()
                    if response == 'y' or response == 'n':
                        break
                    elif response == 's':
                        print()
                        for line in detail_output:
                            if re.search('Reading package lists', line) or re.search('Building dependency tree', line) or re.search('Reading state information', line):
                                continue
                            print(line)
                            if re.search(r'[0-9]* newly installed', line):
                                break
                        print()
                    else:
                        print('Invalid selection.')
                if response == 'y':
                    state = load_medium_state()
                    for package in packages:
                        if package not in state['install_queue'][target]:
                            state['install_queue'][target].append(package)
                            print('Queued ' + package + ' for install')
                        else:
                            print(package + ' already queued for install')
                    save_medium_state(state)
                else: # response == 'n'
                    pass
            else:
                print('Ready to install ' + ", ".join(packages))
                while True:
                    print('Continue with install? Yes (y), No(n), or Show Details (s):', end='')
                    sys.stdout.flush()
                    response = getch()
                    print(response)
                    response = response.lower()
                    if response == 'y' or response == 'n':
                        break
                    elif response == 's':
                        print()
                        for line in detail_output:
                            if re.search('Reading package lists', line) or re.search('Building dependency tree', line) or re.search('Reading state information', line):
                                continue
                            print(line)
                            if re.search(r'[0-9]* newly installed', line):
                                break
                        print()
                    else:
                        print('Invalid selection.')
                if response == 'y':
                    # Override archives parameter with absolute path since apt-get refuses to install from a relative path
                    parms.append('--option')
                    parms.append('Dir::Cache::archives=' + os.path.join(install_medium, 'archives'))
                    proc = subprocess.Popen(parms, env=env)
                    
                    if proc.wait() != 0:
                        print('apt-get failed while installing packages')
                        return -1
                    
                    print ('Installation successful')
                    state = load_medium_state()
                    for package in packages:
                        if package in state['install_queue'][target]:
                            state['install_queue'][target].remove(package)
                    save_medium_state(state)
                    
                    # Re-sync dpkg status info
                    init_action()
                else: # response == 'n'
                    pass
        else:
            state = load_medium_state()
            for package in packages:
                if package in state['install_queue'][target]:
                    state['install_queue'][target].remove(package)
            save_medium_state(state)
            print('All packages already installed/up-to-date')
    
    return 0

def download_action(args):
    install_medium = args.install_medium
    target = args.target
    force = args.force
    allow_unauth = args.allow_unauthenticated
    
    state = load_medium_state()
    if target:
        all_systems = False
        if not os.path.exists(os.path.join(install_medium, 'system_info', target)) or target not in state['download_queue']:
            print('Cannot find target (' + target + ') on medium (' + install_medium + ') check that your spelling is correct and that the target has been initialized on the medium')
            return -1
    else:
        all_systems = True
    
    actions_to_perform = [] # [(hostname, action, additional params.), ...]
    uris_to_download = set()
    for system in (state['download_queue'] if all_systems else [target]):
        if len(state['download_queue'][system]) > 0:
            if not actions_to_perform:
                print('Pending download actions:')
            print('\t' + system + ':')
            action = 'install'
            addtnl_parms = state['download_queue'][system]
            print('\t\t' + action + ' ' + ", ".join(addtnl_parms))
            actions_to_perform.append((system, action, addtnl_parms))
            
            target_info_dir = os.path.join(install_medium, 'system_info', system)
            target_apt_dir = os.path.join(target_info_dir, 'etc', 'apt')
            # Check packages to be downloaded to calculate download size
            # Prepare configuration file to redirect location of /etc/apt in apt-get
            env = setup_config_redirect(os.environ, target_apt_dir)
            
            parms = ['apt-get']
            
            # Set RootDir to installation medium location
            parms.append('--option')
            parms.append('Dir=' + install_medium)
            
            # Load target's apt-medium.conf file
            parms.append('--config-file')
            parms.append(os.path.join(target_apt_dir, 'apt-medium.conf'))
            
            parms.append('install')
            if addtnl_parms:
                parms.extend(addtnl_parms)
            
            try:
                check_parms = list(parms)
                check_parms.append('--print-uris')
                check_parms.append('-qq')
                uris = subprocess.check_output(check_parms, env=env).decode('utf-8')
            except subprocess.CalledProcessError as _:
                print('apt-get failed while checking for needed packages')
                return -1
            
            missing_packages = uris.splitlines()
            missing_packages = [ s.split() for s in missing_packages ]
            missing_packages = map(tuple, missing_packages)
            uris_to_download.update(missing_packages)
    
    if not actions_to_perform:
        print('No pending download actions')
        return 0
    
    # Remove any empty lines from uri set
    try:
        uris_to_download.remove(())
    except KeyError as _:
        pass
    
    total_size = 0
    for item in uris_to_download:
        total_size += int(item[2])
    print('About to download ' + str(len(uris_to_download)) + ' packages totaling ' + '{:,}'.format(total_size) + ' bytes')
    
    while True:
        print('Continue with download? Yes (y), No(n):', end='')
        sys.stdout.flush()
        response = getch()
        print(response)
        response = response.lower()
        if response == 'y' or response == 'n':
            break
        else:
            print('Invalid selection.')
    if response == 'n':
        return 0
    
    success = True
    for target, action, addtnl_params in actions_to_perform:
        target_info_dir = os.path.join(install_medium, 'system_info', target)
        target_apt_dir = os.path.join(target_info_dir, 'etc', 'apt')
        
        # Prepare configuration file to redirect location of /etc/apt in apt-get
        env = setup_config_redirect(os.environ, target_apt_dir)
        
        parms = ['apt-get']
        
        # Set RootDir to installation medium location
        parms.append('--option')
        parms.append('Dir=' + install_medium)
        
        # Load target's apt-medium.conf file
        parms.append('--config-file')
        parms.append(os.path.join(target_apt_dir, 'apt-medium.conf'))
        
        parms.append('--download-only')
        
        if force:
            parms.append('--force-yes')
        else:
            parms.append('--assume-yes')
        
        if allow_unauth:
            parms.append('--allow-unauthenticated')
        
        parms.append(action)
        if addtnl_params:
            parms.extend(addtnl_params)
        
        proc = subprocess.Popen(parms, env=env)
        
        if proc.wait() != 0:
            print('\napt-get failed while downloading packages for target: ' +  target + ' action: ' + action + ' addtnl_params: ' + " ".join(addtnl_params))
            success = False
        else:
            state = load_medium_state()
            for package in addtnl_params:
                state['download_queue'][target].remove(package)
                state['install_queue'][target].append(package)
            save_medium_state(state)
    
    if success:
        print('\nDownload completed successfully')
        return 0
    else:
        print('\nOne or more download actions failed')
        return -1

if __name__ == '__main__':
    main()
