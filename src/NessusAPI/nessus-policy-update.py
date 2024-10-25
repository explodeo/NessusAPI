#!/usr/bin/env python3

import argparse
from argparse import ArgumentError
import json
import os
from getpass import getpass
from sys import argv
import textwrap
import re

def _split_args(argv: list[str], delimiters: list[str]) -> tuple[list, list]:
    parseable_args = []
    remaining_args = []
    for x, arg in enumerate(argv):
        if arg not in delimiters:
            parseable_args.append(arg)
        else:
            remaining_args = argv[x:]
            break
    return parseable_args, remaining_args

def parse_args(argv: list[str]) -> dict:
    commands = {
        'setpasswords': None,
        'configureserver': None,
        'setscanpolicy': None
    }

    args = {}
    parser = argparse.ArgumentParser(
        description="Update a NessusAPI JSON configuration's core settings.",
        usage="USAGE: ./nessus-policy-update.py [-vh] CONFIG {-o OUTFILE | --overwrite} COMMAND ...",
        epilog=textwrap.dedent('''\
            Commands:
                setpasswords: Set credentials for a scan policy
                configureserver: Set server connection settings
                setscanpolicy: Set path to the Nessus scan policy XML 
        ''') 
    )
    parser.add_argument("config", required=True, metavar="CONFIG", help="NessusAPI Policy JSON config")
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--overwrite", action="store_true", help="Overwrite the existing config file.")
    output_group.add_argument("-o", "--outfile", metavar="OUTFILE", help="Path to write the new config to")
    
    setpasswords_parser = argparse.ArgumentParser(description="Replace all passwords in a NessusAPI JSON configuration with real system passwords")
    setpasswords_parser.add_argument("--password_placeholder", required=False, metavar="STRING", default='*', help="Scan config for a custom password placeholder string.")

    configureserver_parser = argparse.ArgumentParser(description="Configure Nessus connection in a NessusAPI JSON configuration with real system passwords")
    configureserver_parser.add_argument('-H', '--host', metavar="HOST", help='IP or hostname to connect to Nessus')
    configureserver_parser.add_argument('-P', '--port', metavar="PORT", default=8834, help='Port to connect to Nessus (default=8834)')
    auth_group = configureserver_parser.add_mutually_exclusive_group()
    auth_group.add_argument('-p', '--usepassword', required=True, action='store_true', help='Prompt for user/password to authenticate to Nessus')
    auth_group.add_argument('-k', '--usekeys', required=True, action='store_true', help='Prompt for authentication keys to authenticate to Nessus')
 
    setscanpolicy_parser = argparse.ArgumentParser(description="Update path to the scan policy to use")
    setscanpolicy_parser.add_argument('policy', metavar="POLICY", required=True, help='Path to the scan policy XML')

    # Parse global args
    remaining_args = argv
    while len(remaining_args) > 0:
        parseable_args, remaining_args = _split_args(argv, commands)
        if len(parseable_args) == 0:
            raise ArgumentError(f'Unknown argument: "{remaining_args[0]}"')
        if parseable_args[0] not in commands:
            args += vars(parser.parse_args(parseable_args))
        else:
            command = parseable_args.pop(0)
            if args.get(command):
                raise ArgumentError(f'Duplicate command found: "{command}"')
            args[command] = vars(parser.parse_args(parseable_args))

    return args

def replace_passwords(dictionary: dict, path: list[str], placeholder_string: str = '*') -> None:
    current_path = path
    for key, value in dictionary.items():
        current_path = path + [key]
        if 'password' in key.lower(): 
            if isinstance(value, str) and (placeholder_string == '*' or value == placeholder_string):
                passwd, confirm_passwd = '', ''
                while not passwd or passwd != confirm_passwd:
                    print("Update Password Configuration:")
                    # print configuration using password (omit nested items)
                    print('.'.join(current_path), '= {') 
                    for k,v in dictionary:
                        if isinstance(k, str) and isinstance(v, str):
                            print(f"  {k}: {v}")
                    print('}')
                    # actually change the password
                    if (user := dictionary.get('username')):
                        passwd = getpass(f'New Password for "{user}": ')
                    else:
                        passwd = getpass(f'New Password": ')
                    passwd = passwd.strip()
                    confirm_passwd = getpass(f'Confirm Password": ')
                    print('\n') # clear the screen a bit
                dictionary[key] = passwd
            elif isinstance(value, dict):
                replace_passwords(value, current_path, placeholder_string=placeholder_string)
            elif isinstance(value, list):
                for x, nested_list in enumerate(value):
                    replace_passwords(value, current_path + [f'[{x}]'], placeholder_string=placeholder_string)

def is_username_valid(username: str) -> bool:
    if (3 <= len(username) <= 20) and re.match(r'^[a-zA-Z][a-zA-Z0-9-_]*[a-zA-Z]'):
        return True
    return False

if __name__ == '__main__':
    args = parse_args(argv)

    if not os.path.exists(args['config']):
        raise OSError("Config file does not exist")
    
    config = json.loads(open(args['config'], 'rb').read())
    
    if command := args.get('setpasswords'):
        placeholder_string = command.get('password_placeholder', '*')
        replace_passwords(config['policies']['credentials'], [], placeholder_string='*')

    elif command := args.get('configureserver'):
        if command.get('usepassword'):
            username = ''
            while not is_username_valid(username):
                username = input('Server Username: ')
            passwd, _passwd = None, None
            while not passwd:
                passwd = getpass("Server Password: ")
                _passwd = getpass("Server Password [Confirm]: ")
                if passwd != _passwd:
                    passwd = None
                    print("Error: Passwords do not match!")
                
            config['server']['credentials'] = {
                "type": "password",
                "username": username,
                "password": passwd
            }
        elif command.get('usekeys'):
            raise NotImplementedError()

    elif command := args.get('setscanpolicy'):
        if not os.path.exists(command['policy']):
            print(f'Cannot find policy file: '{command['policy']}'')
            confirm = input("Update anyways? [Y/n]: ")
            if confirm.lower() in ['y', 'yes']:
                config['policies']['file']= command['policy']
            else:
                print('Policy not updated.')

    outfile_name = args.config if args.get('overwrite') else args['outfile']
    with open(outfile_name, 'w', encoding='ascii') as outfile:
        outfile.write(json.dumps(config, indent=4))

    print('Config updated successfully.')
