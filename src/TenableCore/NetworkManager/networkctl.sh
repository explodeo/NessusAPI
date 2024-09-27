#!/bin/bash

function print_usage(){
    echo "USAGE: network-config.sh [load PROFILE | clear | list]"
    echo "    list: lists mapped connection profiles"
    echo "    clear: removes all existing network configurations"
    echo "    load PROFILE: deletes existing connections and loads a profile"
}

function shutdown_all_connections() {
    echo "Clearing Loaded Connection Profiles"
    nmcli connection show | grep -v NAME | awk '{print $1}' | grep -v lo | xargs -I {} nmcli connection down {} 2>/dev/null
}    
    
function swap_profile(){
    PROFILE=$1
    shutdown_all_connections
    nmcli connection show | grep "$PROFILE" | grep -v NAME | awk '{print $1}' | grep -v lo | xargs -I {} nmcli connection up {}

}

function list_connection_profiles(){
    nmcli connection show
}

function main() {
    COMMAND=$1
    PROFILE=$2
    if [ "$COMMAND" = "list" ]; then
        list_connection_profiles
    elif [ "$COMMAND" = "clear" ]; then
        shutdown_all_connections
    elif [ "$COMMAND" = "load" ]; then
        swap_profile $PROFILE
    else
        echo "ERROR: Unrecognized command"
        print_usage
        exit 1
    fi

    echo ""
    exit 0
}

main "$@"