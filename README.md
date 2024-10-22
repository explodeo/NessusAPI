# NessusAPI

This project creates provides a couple utilities that culminate in a shrunken-down version of [TenableCore + Nessus](https://docs.tenable.com/tenable-core/Nessus/Content/TenableCore/Introduction_Nessus.htm)

It's annoying that without any of the paid options by Tenable, I can't have a monolithic config file that instantiates scans, and imports credentials into a policy file.

***This fixes that***

The only thing you still have to do is install or rebuild plugins (useful for troubleshooting):

```sh
# Install new plugins
$ nessuscli update PLUGINS.tar.gz

# Recompile plugins manually
$ nessusd -R
```

## NessusAPI

An extension of the [pyTenable](https://github.com/tenable/pyTenable) library for Python written for Python 3.9+.

### [`nessusapi.py`](src/NessusAPI/nessusapi.py)
The [nessusapi](src/NessusAPI/nessusapi.py) implements a few methods, namely `import_policy()` and `add_credentials()` which send a PUT/POST request to the Nessus backend API to add credentials to a specific policy.

The [`example-config.json`](src/NessusAPI/configs/example-config.json) is an example config file. The `credentials` object inside it closely mimics the PUT request data that Nessus executes when it adds credentials to a policy file.

### [`nessus-configure.py`](src/NessusAPI/nessus-configure.py)
Creates a `Nessus` API instance using [`pyTenable`](https://github.com/tenable/pyTenable) and loads Policies/Credentials and scans in using a passed `config.json` 

```sh

# Load the Policies/Configs into Nessus
$ nessus-configure -i /path/to/config.json

# Export Complete or Imported Scans
$ nessus-configure -e /path/to/config.json

# You can also programatically interact with nessus:
$ nessus-configure --interactive /path/to/config.json
```
**TODO:** Update nessus-configure to pass args to allow exporting as pdf and csv with all columns.

***NOTE:*** I have a TODO to document the code properly later -- this was a rush job needed for another project of mine.


## "TenableCore" Imitation

This is broken into a couple parts. 

- [TenableCore.sh](src/TenableCore/TenableCore.sh) automates installing a built VDI image in virtualbox.
- [build.sh](build.sh) packages this project into `./dist/installer/TenableCore-Builder.tar.gz` which can be installed using this script from within an Oracle 9 VM
- [build_tenablecore.sh](install/build_tenablecore.sh) extracts the tar and configures Nessus for automation provided you have the right pip packages and RPMs from the [DoD Patch Repository](https://patches.csd.disa.mil/)

## NetworkCtl

A small utility script that wraps `nmcli` to clear, list, and load network profiles.</br>
All you need to do is create a `*.nmconnection` file manually or with `nmtui` and put it in `./TenableCore/NetworkManager` and the `build.sh` will install it with permissions: `rw------- root:root /etc/NetworkManager/system-connections/*.nmconnection` 

Make sure the syntax is good otherwise it won't load.

The main benefit here is `networkctl load PROFILE` will load all profiles starting with `PROFILE` -- a useful utility for loading an interface and all its VLANs simultaneously. 

```sh
# list connection profiles (nmcli con show)
$ networkctl list

# restart networking only loading connections starting with the name eth0_vlan
$ sudo networkctl load eth0_vlan

# clear all network connection profiles
$ sudo networkctl clear
```

***

## Build Process

This is currently in process to be **fully** automated

Recreate distribution files and `scp` them to the VM:
```sh
$ ./build.sh
$ scp ./dist/installer/* root@192.168.56.101:/opt
```

Log into the VM and install/configure ACAS:
```sh
$ cd /opt
$ sudo ./build_tenablecore.sh
```

Watch the prompts in the output to:
- Create and administrative Nessus account
- Set your ACAS classification and other options
- Set 'Enable XML Plugin Attributes' to yes
- exit the nessus configuration script

You can install plugins at this point, load additional configs into `/opt/NessusAPI/configs`, or shut down. </br>
To load plugins, run: `nessuscli update <plugins.tar.gz>`

Remove the build script:
```sh
# rm /tmp/build_tenablecore.sh
```

Once complete, copy the VM virtual disk into `./dist/vm/`. Pack this entire folder to make the portable installation. </br>
You can compress the VM and copy the archive instead using this example: 
```sh
$ tar -czvf ./dist/vm/TenableCore.tar.gz -C "~/VirtualBox VMs/TenableCore" TenableCore.vdi
```

***
***

## Test Setup

Note that the purpose of this VM is to scan things on-demand --- as in you plug it in, scan, export, and delete it.

- VirtualBox 7.1
- 8 GB RAM
- 4 Threads
- No usb, shared folders, or audio
- No optical/floppy drives

The VM in use is Oracle 9.4 with the Unbreakable Enterprise Kernel (UEK). <br>
I install using LVM Thin Partitioning on a 20GB disk. KDump is turned off with no security policy enabled.

***

**Side Note:** *I should **probably** rename this to ACAS-API since it's more fitting and I don't want to get sued by Tenable*
