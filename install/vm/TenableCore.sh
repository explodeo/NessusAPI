#!/bin/sh

# Run this script on the host to install ACAS VM on VirtualBox

VM_DISK_PATH=
INSTALL_DIR=
ADAPTER=

VM_NAME="TenableCore"
CPUS=4
VRAM=16
RAM=16384

INSTALL_VM=
START_VM=

set -e

function usage_start(){
    echo 'USAGE: ./TenableCore.sh start [--name VMNAME] [-h|--help]'
    echo '  Optional:'
    echo '      --name VMNAME: Optional VM Name (Default: TenableCore)'
    echo '      -h|--help: Print this help message'
    echo ''
}

function usage_install(){
    echo 'USAGE: ./TenableCore.sh install VDISK INSTALL_PATH ADAPTER'
    echo '          [--name VM_NAME] [--cpus CPUS] [--ram RAMSIZE] [--vram VRAM]'
    echo '          [--start] [--untar] [-h|--help]'
    echo '  Required:'
    echo '      VDISK: Path to the ACAS Virtual Disk Image or *.tar.gz (VHD/VDI/VMDK)'
    echo '      INSTALL_PATH: Path to install Virtualbox VM'
    echo '      NW_ADAPTER: Network Adapter to bridge to (ex: eth0)'
    echo '  Optional:'
    echo '      --name VMNAME: Optional VM Name (Default: TenableCore)'
    echo '      --cpus CPUS: Allocated CPUs (Default: 4)'
    echo '      --ram RAMSIZE: VM RAM size in MiB (Default: 8192)'
    echo '      --vram VRAM: Video RAM size in MiB (Default: 16)'
    echo '      --start: Starts the VM after creation (Default: False)'
    echo '      -h|--help: Print this help message'
    echo ''
}

function usage_commands(){
    echo 'USAGE: ./TenableCore.sh COMMAND ARGS [-h|--help]'
    echo 'Commands:'
    echo '  install: Installs the TenableCore ACAS Scanner VM'
    echo '  start: Starts the TenableCore ACAS Scanner VM'
    echo '  help: Print This help message'
    echo ''
    echo 'EXAMPLES:'
    echo '  ./TenableCore.sh install VDISK INSTALL_PATH ADAPTER'
    echo '  ./TenableCore.sh start --name "My ACAS VM"'
}

################ ARGPARSE ################

COMMAND=$1
shift

case "$COMMAND" in
    start)
        if [[ "--name" -eq "$1"]]; then
            VM_NAME=$2
        elif [! -z "$1"]; then
            usage_start
            exit 1
        elif [[ "--help" -eq "$1"]]; then
            usage_start
            exit 0
        fi
        ;;
    install)
        if ["$#" -lt 3]; then
            usage_install
            exit 1
        fi

        VM_DISK_PATH=$(realpath "$1")
        INSTALL_DIR=$(realpath "$2")
        ADAPTER=$3
        shift 3

        while [[ "$#" -gt 0 ]]; do
            case $1 in
                --name)
                    VM_NAME=$2
                    shift 2
                    ;;
                --vram)
                    VRAM=$2
                    shift 2
                    ;;
                --ram)
                    RAM=$2
                    shift 2
                    ;;
                --start)
                    START_VM=true
                    shift
                    ;;
                -h|--help)
                    usage_install
                    exit 0
                    ;;
                *)
                    usage_install
                    exit 1
            esac
        done
        ;;
    help|-h|--help)
        usage_commands
        exit 0
        ;;
    *)
        usage_commands
        exit 1
        ;;

esac

################ MAIN ################

if ["$INSTALL_VM" == "true"]; then
    vboxmanage createvm --name "$VMNAME" --register --basefolder "$INSTALL_DIR"
    
    vboxmanage modifyvm "$VMNAME" \
        --cpus "$CPUS" --memory "$RAM" --vram $VRAM \
        --nic1 bridged --bridgeadapter1 "$ADAPTER" \
        --audio none \
        --usb off --usbehci off --usbxhci off \
        --boot1 disk --boot2 none --boot3 none --boot4 none

    vboxmanage storagectl "$VMNAME" \
        --name "SATA Controller" --add sata --controller IntelAhci

    # check if VM is a tar first
    cd $(dirname "$VM_DISK_PATH")
    if [[ "$VM_DISK_PATH" == "*.tar.gz" || $(file "$VM_DISK_PATH") == *"gzip compressed data"*]] ; then
        tar -zxvf "$VM_DISK_PATH" 
        if [[ $? -ez 0 ]]; then 
            rm -f "$VM_DISK_PATH"
        else
            echo "Could not extract VM from *.tar.gz archive."
            exit 1
        fi
    VM_DISK_PATH=$(find . -maxdepth 1 -type f \( -name "*.vmdk" -o -name "*.vdi" -o -name "*.vhd" \) )
    VM_DISK_PATH=$(realpath "$VM_DISK_PATH")
    fi
    cd -

    disk_dir=$(dirname "$VM_DISK_PATH")
    if ["$disk_dir" != "$INSTALL_DIR"]; then
        mv "$VM_DISK_PATH" "$INSTALL_DIR/"
    fi

    vboxmanage storageattach "$VMNAME" --storagectl "SATA Controller" \ 
        --port 0 --device 0 --type hdd --medium "$VM_DISK_PATH"
fi

if ["$START_VM" == "true"]; then
    vboxmanage startvm "$VMNAME" --type gui
fi

exit 0
