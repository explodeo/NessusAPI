#!/bin/bash
# Run this script from within the ACASVM
# this script should be run in the same directory as the 'TenableCore-Builder.tar.gz' file

set -e

# Global Vars
NO_CLEAN=
export INSTALL_TEMPDIR=_ACAS_OS_INSTALL

function usage(){
    echo ''
    echo 'USAGE: ./build_tenablecore.sh [--noclean] [--temp-dir PATH]'
    echo '  Arguments:'
    echo '   --noclean: does not remove extracted files from the "temp-dir"'
    echo '   --temp-dir PATH: specify path to extract tar to (Default: /tmp/_ACAS_OS_INSTALL)'
}

function install_rpms(){
    yum install -y java nessus nmap cdrecord mkisofs tar
    # install rpm extras
    rpm -ivh "$INSTALL_TEMPDIR/install/rpms/jdk-11/*.rpm" || true
}

function configure_nessus(){
    systemctl start nessusd || true
    ln -s /opt/nessus/sbin/nessuscli /usr/sbin/nessuscli || true
    ln -s /opt/nessus/sbin/nessusd /usr/sbin/nessusd || true


    echo "Creating Nessus User Account"
    # need to wait till nessus is fully up here?
    nessuscli adduser || true

    # reset nessus to use SecurityCenter
    systemctl stop nessusd || true
    nessuscli fix --set path_to_java=/bin/java
    nessuscli fix --reset
    nessuscli fetch --security-center

    # start nessus
    systemctl start nessusd || true

}

function configure_networking(){
    # turn off firewalld
    systemctl disable --now firewalld || true

    # install NetworkManager profiles
    cp "$INSTALL_TEMPDIR"/TenableCore/NetworkManager/*.nmconnection /etc/NetworkManager/system-connections/
    chmod 600 /etc/NetworkManager/system-connections/*.nmconnection
    chown root:root /etc/NetworkManager/system-connections/*.nmconnection
    
    # install networkctl
    cp "$INSTALL_TEMPDIR/TenableCore/NetworkManager/networkctl.sh" /opt
    chmod 755 /opt/networkctl.sh
    systemctl restart NetworkManager || true    
}

function install_notes(){
    cp -r "$INSTALL_TEMPDIR/Notes" /opt/
}

function install_api(){
    # install pip packages (includes pyinstaller)
    su acasuser bash -c 'python -m ensurepip'
    sudo -Eu acasuser bash -c '/home/acasuser/.local/bin/pip3 install --no-index --find-links "$INSTALL_TEMPDIR/install/python/oracle/" -r  "$INSTALL_TEMPDIR/NessusAPI/requirements.txt"'
    
    # install nessus-configure src and configs
    mkdir -p /opt/NessusAPI/{bin,src}
    cp -r "$INSTALL_TEMPDIR"/NessusAPI/configs /opt/NessusAPI
    cp "$INSTALL_TEMPDIR"/NessusAPI/*.py /opt/NessusAPI/src/
    
    ln -s /opt/NessusAPI/src/nessus-configure.py /usr/bin/nessus-configure || true
    ln -s /opt/NessusAPI/src/nessus-update-policy.py /usr/bin/nessus-update-policy || true
}

function install_utility_scripts(){
    cp -r "$INSTALL_TEMPDIR"/TenableCore/scripts /opt/
    # force ownership and permissions
    chmod 755 /opt/scripts/*
    chown -R root:root /opt/scripts/*
    # symlink only bins so all users can see it
    ln -s /opt/scripts/bin/* /usr/bin/
    # other scripts get stored here

}

####################### Main #######################

# ensure required file is present first
if [ ! -f "TenableCore-Builder.tar.gz" ]; then
    echo -n "ERROR: TenableCore-Builder.tar.gz not in current directory"
    usage
    exit 1
fi

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --noclean) 
            NO_CLEAN=true ;;
        --temp-dir)
            INSTALL_TEMPDIR="$2"
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "ERROR: Unknown parameter passed: $1";
            usage 
            exit 1
            ;;
    esac
    shift
done

mkdir -p "$INSTALL_TEMPDIR"

install_rpms

tar -xzvf TenableCore-Builder.tar.gz -C "$INSTALL_TEMPDIR"

configure_nessus
configure_networking
install_notes
install_api

echo "Nessus Install Completed"

if [ -z "$NO_CLEAN" ]; then
    rm -rf "$INSTALL_TEMPDIR" TenableCore-Builder.tar.gz build_tenablecore.sh build_tenablecore_oracle7.sh
fi