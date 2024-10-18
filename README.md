# USB Virus Autocleaner

This Python script allows you to perform antivirus scans on USB devices using ClamAV. It includes options to update the ClamAV database, download a test virus file (EICAR), run scans, and remove infected files. The script is designed to run in a terminal and provides a clear menu-driven interface.

## Features

- **Freshclam Database Update (Recommended)**: Updates the ClamAV virus database to ensure you're scanning with the latest virus definitions.
- **Download Test Virus and Scan**: Downloads the EICAR test virus to your USB drive and scans it using ClamAV.
- **Scan USB Device**: Performs a virus scan on a mounted USB device.
- **Scan USB and Remove Infected Files**: Scans a USB device and automatically removes any infected files.
- **Automatic ClamAV Mirror Setup**: Automatically configures the ClamAV mirror for database updates.
- **Clear Old Database**: Removes old ClamAV databases before updating.

## Prerequisites

This script requires the following dependencies:
- **Python 3**: Ensure Python 3 is installed on your machine.
- **ClamAV**: The antivirus software used for scanning.
- **hwinfo**: Used to detect the USB device for scanning.

To install the necessary dependencies, the script will automatically install:
- `clamav`
- `clamav-daemon`
- `hwinfo`

You can also install these dependencies manually:

```bash
sudo apt-get update
sudo apt-get install clamav clamav-daemon hwinfo
```

## Running

To run the script just clone this repository:

```bash
git clone https://github.com/iamromanevil/usb-virus-autocleaner.git
cd usb-virus-autocleaner
```

Make the script executable:

```bash
chmod +x usb-virus-autocleaner.py
```

Run the script:

```bash
sudo python3 usb-virus-autocleaner.py
```
