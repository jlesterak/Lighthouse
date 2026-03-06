#!/bin/bash
# Lighthouse Unified Setup Script
# Provides an interactive menu to download content, readers, and build the Live OS/USB

set -e

# Support curling the bash script directly
if [ ! -d "Lighthouse/.git" ] && [ ! -d ".git" ]; then
    echo "Cloning Lighthouse repository..."
    git clone https://github.com/jlesterak/Lighthouse.git
    cd Lighthouse
fi

# Ensure we're in the right directory if script was curled into the root
if [ -d "Lighthouse" ] && [ -f "Lighthouse/setup.sh" ]; then
    cd Lighthouse
fi

echo "================================================="
echo " Lighthouse Initialization & Build Tool"
echo "================================================="

while true; do
    echo ""
    echo "Please select an option:"
    echo "1) Download Offline Content (ZIMs)"
    echo "2) Download Readers (Kiwix)"
    echo "3) Build Live OS ISO"
    echo "4) Flash Live OS & Content to USB"
    echo "5) Exit"
    echo ""
    read -p "Enter choice [1-5]: " choice
    
    case $choice in
        1)
            echo ""
            echo "Launching ZIM Downloader..."
            # Check for python3
            if ! command -v python3 &> /dev/null; then
                echo "Python 3 is required. Please install it."
                exit 1
            fi
            python3 updater.py
            ;;
        2)
            echo ""
            echo "Launching Reader Downloader..."
            ./get_readers.sh
            ;;
        3)
            echo ""
            echo "Launching Live OS ISO Builder..."
            sudo ./build_iso.sh
            ;;
        4)
            echo ""
            echo "Launching USB Flasher..."
            read -p "Enter the target USB device (e.g., /dev/sdX): " usb_device
            if [ -z "$usb_device" ]; then
                echo "Invalid device."
            else
                sudo ./build_usb.sh "$usb_device"
            fi
            ;;
        5)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid choice. Please enter 1-5."
            ;;
    esac
done
