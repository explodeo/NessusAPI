#!/bin/bash

# Check if required commands are available
command -v mkisofs >/dev/null 2>&1 || { echo >&2 "mkisofs is not installed. Aborting."; exit 1; }
command -v cdrecord >/dev/null 2>&1 || { echo >&2 "cdrecord is not installed. Aborting."; exit 1; }

# Check if at least one file or directory is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 file1 file2 ... fileN directory1 directory2 ..."
    exit 1
fi

# Create a temporary directory for the ISO image
TEMP_DIR=$(mktemp -d)
ISO_IMAGE="$TEMP_DIR/image.iso"

# Create the ISO image from the provided files and directories
mkisofs -file-mode 777 -o "$ISO_IMAGE" -J -R "$@"

# Check if mkisofs succeeded
if [ $? -ne 0 ]; then
    echo "Failed to create ISO image. Aborting."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Burn the ISO image to the CD/DVD and finalize it
cdrecord dev=/dev/sr0 -finalize "$ISO_IMAGE"

# Check if cdrecord succeeded
if [ $? -ne 0 ]; then
    echo "Failed to burn the image to CD/DVD."
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Successfully burned the files and directories to CD/DVD, finalized it, and ensured Windows compatibility."

# Clean up
rm -rf "$TEMP_DIR"
