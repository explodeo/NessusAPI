#!/bin/sh

# Run this script from the project root (outside of ./src)
# This script packages the following into a *.tar.gz to install TenableCore
#   - Nessus/ACAS RPMs - packs 'acas-configure', 'dialog', and 'Nessus' RPMs
#   - networkctl - NetworkManager connections and the 'networkctl' utility
#   - NessusAPI - Utilities to automate installing Nessus and programmatically connecting to the API
#       - pip packages are also packed, but removed after running 'build_tenablecore.sh'
#   - SCAP - Nick Giannini's SCAP automation scripts and the SCAP utilities
#   - Notes - ACAS and SCAP notes

# A second *.tar.gz is created that compresses the TenableCore VM

function usage_commands(){
    echo 'USAGE: ./build.sh COMMAND [ARGS]'
    echo 'Commands:'
    echo '  installer: Builds tar.gz distribution for custom installs'
    echo '  vm: Builds a VM from a tar distribution remotely from a base VMDK'
    echo '  all: Builds a tar distribution and installs it in a base VMDK'
    echo '  help: Print This help message'
    echo ''
    echo 'EXAMPLES:'
    echo '  ./build.sh install TODO'
    echo '  ./build.sh vm TODO'
    echo '  ./build.sh all TODO'
}


function usage_installer(){
    echo 'USAGE: ./build.sh install [ARGS]'
    echo 'Commands:'
    echo '  help: Print This help message'
    echo ''
    echo 'EXAMPLES:'
    echo '  ./build.sh install TODO'
}

function usage_all(){
    echo 'USAGE: ./build.sh all [ARGS]'
    echo 'Commands:'
    echo '  help: Print This help message'
    echo ''
    echo 'EXAMPLES:'
    echo '  ./build.sh install TODO'
}

function build_tar_local_installer(){
    # The final TGZ and install script is outputted into the ./dist folder
    mkdir -p ./dist/installer

    find . -type f \( -name "*.sh" -o -name "*.py" \) -exec dos2unix {} +

    tar -czvf ./dist/installer/TenableCore-Builder.tar.gz \
        --exclude='*/VM' \
        --exclude='*/example-plugins' \
        --exclude="*/install/python/linux" \
        --exclude='*/install/python/win' \
        --exclude='*/install/python/win' \
        --exclude='*/install/utils' \
        --exclude='*.exe' \
        --exclude='*.iso' \
        --exclude='*/install/build_tenablecore.sh' \
        -C src NessusAPI SCAP TenableCore Notes -C .. install

        cp ./install/utils/tar*.rpm ./dist/installer
        cp ./install/utils/build_tenablecore.sh ./dist/installer
}

function build_vm_dist(){
    # cp ./install/utils/TenableCore.sh ./dist/vm/
    # tar -czvf ./dist/vm/TenableCore.tar.gz -C "~/VirtualBox VMs/TenableCore" TenableCore.vmdk
    echo 'TODO: NOT IMPLEMENTED'    
}

######## MAIN ########

# COMMAND=$1
# shift

# case "$COMMAND" in
#     installer)
#         usage_installer
#         ;;
#     vm)
#         usage_vm
#         ;;
#     all)
#         usage_all
#         ;;
#     help)
#         usage
#         ;;
#     *)
#         usage
#         ;;
# esac


build_tar_local_installer