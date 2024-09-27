#!/usr/bin/env python3

import os
import code
from sys import argv
from nessusapi import NessusAPI

if __name__ == "__main__":
    if any(arg in ['-h', '--help'] for arg in argv):
        print(f"USAGE: {argv[0]} /path/to/config.json [-h|--help] [--interactive] [--initialize]")
        exit(0)
    if not os.path.exists(argv[1]):
        raise ValueError("ERROR: Config file does not Exist")
    nessus = NessusAPI(file=argv[1], initialize=('--initialize' in argv))
    if '--interactive' in argv:
        from pprint import pprint
        printvars = lambda obj: pprint(vars(obj))
        n = nessus.Nessus
        code.interact(local=locals())
    nessus.logout()
