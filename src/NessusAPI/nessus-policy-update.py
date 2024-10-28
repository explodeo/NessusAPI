#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentError, RawTextHelpFormatter
import json
import os
from getpass import getpass
from sys import argv
import textwrap
import re
from time import sleep

def _split_args(argv: list[str], delimiters: list[str]) -> tuple[list, list]:
    parseable_args = []
    remaining_args = []
    for x, arg in enumerate(argv):
        if arg not in delimiters:
            parseable_args.append(arg)
        else:
            remaining_args = argv[x:]
            if not parseable_args: # only commands left to process
                parseable_args, remaining_args = remaining_args, parseable_args
            break
    return parseable_args, remaining_args

def parse_args(argv: list[str]) -> dict:
    commands = {
        'setpasswords': None,
        'configureserver': None,
        'setscanpolicy': None
    }

    args = {}
    parser = ArgumentParser(
        description="Update a NessusAPI JSON configuration's core settings.",
        usage="USAGE: ./nessus-policy-update.py [-vh] CONFIG {-o OUTFILE | --overwrite} COMMAND ...",
        formatter_class=RawTextHelpFormatter,
        epilog=textwrap.dedent('''COMMAND:
    setpasswords:    Set credentials for a scan policy
    configureserver: Set server connection settings
    setscanpolicy:   Set path to the Nessus scan policy XML
    ''')
    )
    parser.add_argument("config", metavar="CONFIG", help="NessusAPI Policy JSON config")
    parser.add_argument("--policies", metavar="POLCYNAME", nargs='*', default=['*'], help="Choose a specific policy to update in the JSON config (default=*)")
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--overwrite", action="store_true", help="Overwrite the existing config file.")
    output_group.add_argument("-o", "--outfile", metavar="OUTFILE", help="Path to write the new config to")
    
    setpasswords_parser = ArgumentParser(description="Replace all passwords in a NessusAPI JSON configuration with real system passwords")
    setpasswords_parser.command = "setpasswords"
    setpasswords_parser.add_argument("--password_placeholder", required=False, metavar="STRING", default='*', help="Scan config for a custom password placeholder string.")

    configureserver_parser = ArgumentParser(description="Configure Nessus connection in a NessusAPI JSON configuration with real system passwords")
    configureserver_parser.command = "configureserver"
    configureserver_parser.add_argument('-H', '--host', metavar="HOST", help='IP or hostname to connect to Nessus')
    configureserver_parser.add_argument('-P', '--port', metavar="PORT", default=8834, help='Port to connect to Nessus (default=8834)')
    auth_group = configureserver_parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument('-p', '--usepassword', action='store_true', help='Prompt for user/password to authenticate to Nessus')
    auth_group.add_argument('-k', '--usekeys', action='store_true', help='Prompt for authentication keys to authenticate to Nessus')
 
    setscanpolicy_parser = ArgumentParser(description="Update path to the scan policy to use")
    setscanpolicy_parser.command = "setscanpolicy"
    setscanpolicy_parser.add_argument('policy', metavar="POLICYXML", help='Path to the scan policy XML')

    # Parse global args
    remaining_args = argv
    while len(remaining_args) > 0:
        parseable_args, remaining_args = _split_args(remaining_args, commands)
        if len(parseable_args) == 0:
            raise ArgumentError(None, f'Unknown argument: "{remaining_args[0]}"')
        if parseable_args[0] not in commands:
            args.update(vars(parser.parse_args(parseable_args)))
        else:
            command = parseable_args.pop(0)
            if args.get(command):
                raise ArgumentError(None, f'Duplicate command found: "{command}"')
            if command == configureserver_parser.command:
                command_parser = configureserver_parser
            elif command == setpasswords_parser.command:
                command_parser = setpasswords_parser
            elif command == setscanpolicy_parser.command:
                command_parser = setscanpolicy_parser
            else:
                raise ArgumentError(None, f"Error: Command not found: '{command}'")
            args[command] = vars(command_parser.parse_args(parseable_args))

    # raise error if no commands used
    if not any([args.get(c) for c in commands]):
        raise ArgumentError(None, "Error: No Command Specified")

    return args

def _replace_passwords(dictionary: dict, path: list[str], placeholder_string: str = '*') -> None:
    current_path = path
    for key, value in dictionary.items():
        current_path = path + [key]
        if isinstance(value, str) and key.lower().endswith('password') and (placeholder_string == '*' or value == placeholder_string):
                passwd, confirm_passwd = '', '_'
                while not passwd or passwd != confirm_passwd:
                    print("Update Password Configuration:")
                    # print configuration using password (omit nested items)
                    print('.'.join(current_path), '= {') 
                    for k,v in dictionary.items():
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
                    if passwd != confirm_passwd:
                        print("ERROR: Passwords do not match")
                        sleep(1)
                dictionary[key] = passwd
        elif isinstance(value, dict):
            _replace_passwords(value, current_path, placeholder_string=placeholder_string)
        elif isinstance(value, list) and len(value) > 0 and  isinstance(value[0], dict):
            for x, nested in enumerate(value):
                _replace_passwords(nested, current_path + [f'[{x}]'], placeholder_string=placeholder_string)

def is_username_valid(username: str) -> bool:
    if (3 <= len(username) <= 20) and re.match(r'^[a-zA-Z][a-zA-Z0-9-_]*[a-zA-Z]', username):
        return True
    return False

if __name__ == '__main__':
    args = parse_args(argv[1:])
    print(args)
    if not os.path.exists(args['config']):
        raise OSError("Config file does not exist")
    
    config = json.loads(open(args['config'], 'rb').read())
    scan_policies = []
    if args['policies'] == ['*']:
        scan_policies = config['policies']
    elif args['policies'] != ['*']:
        policies_userinput = set(args['policies'])
        for pol in config['policies']:
            if any([passed_pol_name not in pol['name'] for passed_pol_name in policies_userinput]):
                raise ValueError(f'ERROR: Invalid policy name used"')
            scan_policies.append(pol)
    for scan_policy in scan_policies:
        if command := args.get('setpasswords'):
            _replace_passwords(scan_policy['credentials'], [], placeholder_string=command.get('password_placeholder', '*'))

        elif command := args.get('configureserver'):
            if host:= command.get('host'):
                config['server']['host'] = host
            if port:= command.get('port'):
                config['server']['port'] = port
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
                print(f'Cannot find policy file: "{command["policy"]}"') 
                confirm = input("Update anyways? [Y/n]: ")
                if confirm.lower() in ['y', 'yes']:
                    scan_policy['file'] = command['policy']
                else:
                    print('Policy not updated.')
            else:
                scan_policy['file'] = os.path.realpath(command['policy'])
    outfile_name = args['config'] if args.get('overwrite') else args['outfile']
    with open(outfile_name, 'w', encoding='ascii') as outfile:
        outfile.write(json.dumps(config, indent=4))

    print('Config updated successfully.')
