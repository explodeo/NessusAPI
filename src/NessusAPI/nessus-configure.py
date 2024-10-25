#!/usr/bin/env python3

import code
import argparse
from argparse import ArgumentError
import os
from getpass import getpass
from nessusapi import NessusAPI

def interact(nessus: NessusAPI) -> None:
    n = nessus.Nessus
    code.interact(local=locals())

def parse_args() -> None:
    parser = argparse.ArgumentParser(description="A command-line interface for nessus. Used to initialize/export a nessus instance or interact with the API.")
    parser.add_argument('-v', '--verbose', help='Add Verbosity')
    login_group = parser.add_argument_group("Connection Info")
    login_group.add_argument('-c', '--config', metavar="CONFIG", help='JSON Nessus Credential/Policy/Scan configuration file')
    login_group.add_argument('-U', '--user', metavar="USERNAME", help='User to authenticate to Nessus')
    login_group.add_argument('-H', '--host', metavar="HOST", help='IP/hostname of the Nessus instance')
    login_group.add_argument('-p', '--port', metavar="PORT", help='Port to connect to Nessus')

    subparser = parser.add_subparsers(title='Commands', dest='command')

    export_parser = subparser.add_parser('export', description="Export Nessus Scans to Directory")
    export_parser.add_argument('-o', '--outdir', metavar="OUTPUT_DIR", help='Directory to export scan results to')
    export_parser.add_argument('-f', '--format', metavar="FMT", nargs='*', default=['nessus'], required=False, help='Formats for scan exports: nessus, pdf, csv, html (default=nessus)')
    export_parser.add_argument('--scan_folder', metavar="FOLDER", required=False, help='Export all scans from a folder in Nessus')

    init_parser = subparser.add_parser('init', description='Initialize Nessus Policies/Credentials and Scans')
    init_parser.add_argument('-e', '--exec', action='store_true', help="Inits Nessus and executes all scans from the config")

    exec_parser = subparser.add_parser('exec', description='Use Python to interact with Nessus')
    exec_parser.add_argument('-f', '--folder', metavar="SCAN_FOLDER", help='Execute all scans in this folder')
    exec_parser.add_argument('-s', '--scan', metavar="SCAN_NAME", nargs='*', help='Execute one or more scans with this name')

    subparser.add_parser('interact', description='Use Python to interact with Nessus')
    
    args = parser.parse_args()

    if args.verbose:
        print(args)

    # login error checking
    if not ((args.user and args.host and args.port) or args.config):
        raise ArgumentError(message="Must specify either a config file and/or a user with a host/port")

    # check config existence        
    if args.config:
        if not os.path.exists(args.config):
            raise FileNotFoundError("ERROR: Config file does not Exist")

    return args

def init() -> NessusAPI:
    args = parse_args()

    nessus = None
    if args.config:
        if args.user:
            nessus = NessusAPI(file=args.config, initialize=(args.command == 'init'),
                                host=args.host, port=args.port,
                                credentials={
                                    "type": "password",
                                    "username": args.user,
                                    "password": getpass("Nessus Password: ")
                                })
        else:
            nessus = NessusAPI(file=args.config, initialize=(args.command == 'init'))

    elif args.host and args.user:
        if args.command == 'initialize':
            raise ArgumentError("Cannot initialize Nessus scans/policies without a config file.")
        if not args.port: 
            args.port = 8834
        nessus = NessusAPI(host=args.host,
                            port=args.port,
                            credentials={
                                "type": "password",
                                "username": "acasuser",
                                "password": getpass("Nessus Password: ")
                            })
    else:
        pass # this error (lack of connection info) was checked earlier

    if args.command == "init":
        if args.exec:
            raise NotImplementedError("Auto execution of scans after init is not implemented")
    elif args.command == "exec":
        raise NotImplementedError("CLI execution of nessus scans is not implemented")

    elif args.command == "export":
        nessus.export_all_scans(outdir=args.outdir, export_formats=[f.lower() for f in args.format], scan_folder=args.scan_folder)

    elif args.command == 'interact':
        interact(nessus)

    else:
        raise ArgumentError("Unsupported Command") # control never reaches here

    return nessus


if __name__ == "__main__":
    nessus = None
    try:
        nessus = init()
    except Exception as e:
        print(e)
        if nessus:
            nessus.logout()
