# NessusAPI

This project creates provides a couple utilities that culminate in a shrunken-down version of [TenableCore + Nessus](https://docs.tenable.com/tenable-core/Nessus/Content/TenableCore/Introduction_Nessus.htm)

It's annoying that without any of the paid options by Tenable, I can't have a monolithic config file that instantiates scans, and imports credentials into a policy file.

**This fixes that**

## NessusAPI

An extension of the [pyTenable](https://github.com/tenable/pyTenable) library for Python written for Python 3.9+.

### [`nessusapi.py`](src/NessusAPI/nessusapi.py)
The [nessusapi](src/NessusAPI/nessusapi.py) implements a few methods, namely `import_policy()` and `add_credentials()` which send a PUT/POST request to the Nessus backend API to add credentials to a specific policy.

### [`nessus-configure.py`](src/NessusAPI/nessus-configure.py)
Creates a `Nessus` API instance using [`pyTenable`](https://github.com/tenable/pyTenable) and loads Policies/Credentials and scans in using a passed `config.json` 

The [`example-config.json`](src/NessusAPI/configs/example-config.json) is an example config file. The `credentials` object inside it closely mimics the PUT request data that Nessus executes when it adds credentials to a policy file.

***NOTE:*** I have a TODO to document the code properly later -- this was a rush job needed for another project of mine.

## "TenableCore" Imitation

This is broken into a couple parts. 

- [TenableCore.sh](src/TenableCore/TenableCore.sh) automates installing a built VDI image in virtualbox.
- [build.sh](build.sh) packages this project into `./dist/installer/TenableCore-Builder.tar.gz` which can be installed using this script from within an Oracle 9 VM
- [build_tenablecore.sh](install/build_tenablecore.sh) extracts the tar and configures Nessus for automation provided you have the right pip packages and RPMs from the [DoD Patch Repository](https://patches.csd.disa.mil/)

## NetworkCtl

A small utility script that wraps `nmcli` to clear, list, and load network profiles.</br>
The main benefit here is `networkctl load PROFILE` will load all profiles starting with `PROFILE` -- a useful utility for loading an interface and all its VLANs simultaneously. 

***
***

**Side Note:** *I should **probably** rename this to ACAS-API since it's more fitting and I don't want to get sued by Tenable*
