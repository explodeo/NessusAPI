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
    # install java first per https://docs.tenable.com/nessus/Content/SoftwareRequirements.htm
    rpm -ivh "$INSTALL_TEMPDIR/install/rpms/jdk-11/*.rpm" || true
    rpm -i "$INSTALL_TEMPDIR/install/rpms/acas/CM307352_Nessus-10.7.3-el8.x86_64.rpm" || true
    rpm -i "$INSTALL_TEMPDIR/install/rpms/acas/dialog-1.3-32.20210117.el9.x86_64.rpm" || true
    rpm -i "$INSTALL_TEMPDIR/install/rpms/acas/CM306733_acas_configure-24.03-4.noarch.rpm" || true
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

    # echo "Reconfiguring Nessus to ACAS. Please Wait"
    /opt/acas/bin/config-scripts/ns-conf.sh

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
    
    ln -s /opt/networkctl.sh /usr/bin/networkctl || true
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
    
    # pip3 install --no-index --find-links "$INSTALL_TEMPDIR/install/python/oracle/" -r  "$INSTALL_TEMPDIR"/install/python/oracle/*
    # compile nessus-configure.py
    # cd /opt/NessusAPI/src
    # pyinstaller --onefile --distpath /opt/NessusAPI/bin --workpath /tmp --specpath /tmp
    # cd -

    # ln -s /opt/NessusAPI/bin/nessus-configure /usr/bin/nessus-configure
    ln -s /opt/NessusAPI/src/nessus-configure.py /usr/bin/nessus-configure || true
}

function install_scap_tools(){
    # TODO
    echo "TODO: Install SCAP Automation Tools"
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

if ! command -v tar &> /dev/null; then
   rpm -i tar-1.34-6.el9_4.1.x86_64.rpm
fi

tar -xzvf TenableCore-Builder.tar.gz -C "$INSTALL_TEMPDIR"

install_rpms
configure_nessus
configure_networking
install_notes
install_api
install_scap_tools

echo "Nessus Install Completed"

if [ -z "$NO_CLEAN" ]; then
    rm -rf "$INSTALL_TEMPDIR" TenableCore-Builder.tar.gz tar-1.34-6.el9_4.1.x86_64.rpm build_tenablecore.sh
fi