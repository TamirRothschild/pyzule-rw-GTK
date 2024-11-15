#!/bin/bash

# Hello
echo "Hello now we will install Cyan with full GUi support, if you wish to stop at any time press Ctrl and c at the same time(^c)"
echo "Good Luck"

# Check for required commands
REQUIRED_CMDS=("curl" "gcc" "pipx" "pkg-config")

for cmd in "${REQUIRED_CMDS[@]}"; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed. Please install it and try again."
        exit 1
    fi
done


# installing pyzule-rw / cyan
echo "Installing pyzule-rw/cyan.."
pipx install --force https://github.com/asdfzxcvbn/pyzule-rw/archive/main.zip

# URL to the latest source code
SOURCE_URL="https://raw.githubusercontent.com/TamirRothschild/pyzule-rw-GTK/refs/heads/main/cyan/GTK/pyzule-rw(cyan)_GTK.c"
SOURCE_FILE="pyzule-rw(cyan)_GTK.c"
OUTPUT_FILE="cyan-GUi"


# Check if GTK libraries are installed
function check_gtk() {
    if ! pkg-config --exists gtk+-3.0; then
        echo "Error: GTK+-3.0 development libraries are not installed."
        echo "Install the GTK development package using your package manager."
        exit 1
    fi
}


# Download the latest source code using curl
echo "Downloading the latest source code..."
curl -L -o "$SOURCE_FILE" "$SOURCE_URL"

# Check if download was successful
if [ $? -ne 0 ]; then
    echo "Failed to download the source code."
    exit 1
fi


# Compile the downloaded source code with gcc
echo "Compiling the latest GUi for cyan..."
sudo gcc -o "$OUTPUT_FILE" "$SOURCE_FILE" `pkg-config --cflags --libs gtk+-3.0`


# Check if compilation succeeded
if [ $? -eq 0 ]; then
    echo "Compilation successful. The executable is named $OUTPUT_FILE at $(pwd)/$OUTPUT_FILE"
else
    echo "Compilation failed."
    exit 1
fi


# First run
echo "Installtion finished, you can run it with ./$OUTPUT_FILE"
echo "Running Cyan-GUi for the first time"
./$OUTPUT_FILE 
exit 0
