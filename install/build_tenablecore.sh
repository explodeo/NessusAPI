#!/bin/sh
# Run this script from within the ACASVM
# this script should be run in the same directory as the 'TenableCore-Builder.tar.gz' file

# exit on error
set -e

INSTALL_TEMPDIR=/tmp/_ACAS_OS_INSTALL

function usage(){
    echo ''
    echo 'USAGE: ./build_tenablecore.sh [--noclean] [--temp-dir PATH]'
    echo '  Arguments:'
    echo '   --noclean: does not remove extracted files from the "temp-dir"'
    echo '   --temp-dir PATH: specify path to extract tar to (Default: /tmp/_ACAS_OS_INSTALL)'
}

function install_rpms(){
    rpm -i "$INSTALL_TEMPDIR/rpms/CM307352_Nessus-10.7.3-el8.x86_64.rpm"
    rpm -i "$INSTALL_TEMPDIR/rpms/dialog-1.3-32.20210117.el9.x86_64.rpm"
    rpm -i "$INSTALL_TEMPDIR/rpms/CM306733_acas_configure-24.03-4.noarch"
}

function configure_nessus(){
    systemctl start nessusd
    ln -s /opt/nessus/sbin/nessuscli /usr/sbin/nessuscli

    echo "Creating Nessus User Account"
    nessuscli adduser

    # run ns-conf.sh
    echo "Reconfiguring Nessus to ACAS. Please Wait"
    /opt/acas/bin/config-scripts/ns-conf.sh & sleep 60 && kill -9 $(pgrep ns-conf.sh) &
    echo "Done"
}

function configure_networking(){
    # turn off firewalld
    systemctl disable --now firewalld

    # install NetworkManager profiles
    cp "$INSTALL_TEMPDIR/NetworkManager/*.nmconnection" /etc/NetworkManager/system-connections/
    chmod 600 /etc/NetworkManager/system-connections/*.nmconnection
    chown root:root /etc/NetworkManager/system-connections/*.nmconnection
    
    # install networkctl
    cp "$INSTALL_TEMPDIR/NetworkManager/networkctl.sh" /opt
    chmod 755 /opt/networkctl.sh
    systemctl restart NetworkManager
    
    ln -s /opt/networkctl.sh /usr/bin/networkctl
}

function install_notes(){
    cp -r "$INSTALL_TEMPDIR/Notes" /opt/
}

function install_api(){
    # install pip packages (includes pyinstaller)
    pip install --no-index --find-links "$INSTALL_TEMPDIR/install/python/oracle/" -r  "$INSTALL_TEMPDIR/NessusAPI/requirements.txt"

    # install nessus-configure src and configs
    mkdir -p /opt/NessusAPI/{bin,src}
    cp -r "$INSTALL_TEMPDIR/NessusAPI/config" /opt/NessusAPI
    cp "$INSTALL_TEMPDIR/NessusAPI/*.py" /opt/NessusAPI/src/
    
    # compile nessus-configure.py
    cd /opt/NessusAPI/src
    pyinstaller --onefile --distpath /opt/NessusAPI/bin --workpath /tmp --specpath /tmp
    cd -

    ln -s /opt/NessusAPI/bin/nessus-configure /usr/bin/nessus-configure
}

function install_scap_tools(){
    # TODO
    echo "TODO: Install SCAP Automation Tools"
}

####################### Main #######################

# ensure required file is present first
if [ ! -f "TenableCore-Builder.tar.gz" ]; then
    echo -n "ERROR: "
    usage
    exit 1
fi

NO_CLEAN=false
INSTALL_TEMPDIR=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --noclean) 
            NO_CLEAN=true ;;
            ;;
        --temp-dir) 
            INSTALL_TEMPDIR="$2"; 
            shift
            ;;
        --help|-h)
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

tar -xzvf -C "$INSTALL_TEMPDIR"

install_rpms
configure_nessus
configure_networking
install_notes
install_api
install_scap_tools

if [ "$NO_CLEAN" = "false"]; then
    rm -rf "$INSTALL_TEMPDIR"
fi