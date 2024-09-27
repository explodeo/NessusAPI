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

# The final TGZ and install script is outputted into the ./dist folder

find . -type f \( -name "*.sh" -o -name "*.py" \) -exec dos2unix {} +

tar -czvf ./dist/installer/TenableCore-Builder.tar.gz \
    --exclude='*/VM' \
    --exclude='*/example-plugins' \
    --exclude="*/install/python/linux" \
    --exclude='*/install/python/win' \
    --exclude='*/install/python/win' \
    --exclude='*.exe' \
    --exclude='*.iso' \
    --exclude='*/install/build_tenablecore.sh' \
    -C src NessusAPI SCAP TenableCore Notes -C .. install
    # -C ./src/NessusAPI . -C ./src/SCAP . -C ./src/TenableCore/NetworkManager . -C ./src/Notes  . -C ./install .

cp ./install/build_tenablecore.sh ./dist/installer