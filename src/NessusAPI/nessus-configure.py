#!/usr/bin/env python3

import code
import argparse
import os
from sys import argv
from nessusapi import NessusAPI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A command-line interface for nessus. Used to initialize/export a nessus instance or interact with the API.")
    parser.add_argument('config', metavar="CONFIG")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-i', "--initialize", action='store_true', help="Initialize Nessus Scans/Policies.")
    group.add_argument('-e', "--export", nargs='*', metavar=("OUTDIR", "SCANFOLDER"), help="Export all complete scans to this directory. Can limit scans based on folder.")
    group.add_argument('--interactive', action='store_true', help="Interact directly with the Nessus API. (Use locals() to see vars)")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        raise ValueError("ERROR: Config file does not Exist")

    nessus = NessusAPI(file=args.config, initialize=args.initialize)
    if args.export:
        nessus.export_all_scans(outdir=args.export)
    if args.interactive:
        from pprint import pprint
        printvars = lambda obj: pprint(vars(obj))
        n = nessus.Nessus
        code.interact(local=locals())

    nessus.logout()
