import subprocess
import os
import re

# Define ANSI color codes for styling
HEADER_COLOR = "\033[93m"  # Yellow
MENU_COLOR = "\033[96m"    # Cyan
PROMPT_COLOR = "\033[93m"  # Yellow (same as header)
ERROR_COLOR = "\033[91m"   # Red for freshclam option
RESET_COLOR = "\033[0m"    # Reset to default color

def print_message(message):
    """Prints message with [+] prefix"""
    print(f"[+] {message}")

def print_header(message):
    """Print header with a specific color"""
    print(f"{HEADER_COLOR}[+] {message}{RESET_COLOR}")

def print_menu_option(message, color=MENU_COLOR):
    """Print menu options with a specific color"""
    print(f"{color}{message}{RESET_COLOR}")

def print_prompt(message):
    """Print prompt with a specific color"""
    print(f"{PROMPT_COLOR}{message}{RESET_COLOR}")

def run_command(command):
    """Run a command and capture its output"""
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result
    except Exception as e:
        print_message(f"Exception while running command: {e}")
        return None

def check_installation(command, package_list):
    """Check if a command exists, if not install the necessary packages non-interactively"""
    try:
        # Use 'which' to check if the command exists in the system's PATH
        result = run_command(["which", command])
        if not result.stdout.strip():
            print_message(f"{command} is not installed. Installing required packages...")
            run_command(["sudo", "apt", "update"])
            # Run non-interactive installation for each package in the list
            for package in package_list:
                print_message(f"Installing {package}...")
                install_result = run_command([
                    "sudo", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", package
                ])

                if install_result.returncode != 0:
                    print_message(f"ERROR: Failed to install {package}. Error output:\n{install_result.stderr.strip()}")
                else:
                    print_message(f"{package} installed successfully.")

            # Verify if the command was installed successfully
            result = run_command(["which", command])
            if result.stdout.strip():
                print_message(f"{command} installed successfully.")
                return True
            else:
                print_message(f"ERROR: Failed to install {command}. Please check manually.")
                return False
        else:
            print_message(f"{command} is already installed and available.")
            return True
    except Exception as e:
        print_message(f"Exception while checking/installing {command}: {e}")
        return False

def update_freshclam():
    """Run freshclam and handle errors related to log file locking or initialization"""
    try:
        # Automatically set the ClamAV mirror if necessary
        print_message("Setting the ClamAV mirror to the default (db.us.clamav.net)...")
        freshclam_config_file = "/etc/clamav/freshclam.conf"
        with open(freshclam_config_file, 'r') as file:
            config_lines = file.readlines()
        
        with open(freshclam_config_file, 'w') as file:
            for line in config_lines:
                # Ensure the mirror is set to the correct value
                if line.strip().startswith("DatabaseMirror"):
                    file.write("DatabaseMirror db.us.clamav.net\n")
                else:
                    file.write(line)
        
        print_message("Updating ClamAV database with freshclam...")
        result = run_command(["sudo", "freshclam"])
        output = result.stderr.strip()

        if "Resource temporarily unavailable" in output or "Problem with internal logger" in output:
            print_message("ERROR: Log file is locked or unavailable. Attempting to resolve...")
            print_message("Attempting to remove lock and fix freshclam log issues...")
            # Remove log file to release the lock
            run_command(["sudo", "rm", "/var/log/clamav/freshclam.log"])
            print_message("Log file removed. Retrying freshclam update...")
            # Retry freshclam after removing the log
            result = run_command(["sudo", "freshclam"])
            if result.returncode == 0:
                print_message("ClamAV database successfully updated.")
            else:
                print_message(f"ERROR: freshclam failed again with message:\n{result.stderr.strip()}")
        elif result.returncode == 0:
            print_message("ClamAV database successfully updated.")
        else:
            print_message(f"ERROR: freshclam failed with message:\n{output}")

    except Exception as e:
        print_message(f"Exception while running freshclam: {e}")

def run_clamscan_with_filtered_output(remove_infected=False):
    """Run clamscan and show only inspected, infected, and removed files"""
    command = ["sudo", "clamscan", "-r", "/mnt/usb"]
    if remove_infected:
        command.append("--remove=yes")  # Add the --remove option for infected files

    try:
        result = run_command(command)
        output = result.stdout.splitlines()
        removed_files = []  # To store the names of removed files
        total_removed = 0  # To count the number of removed files

        for line in output:
            # Display lines that report infected, removed, or scanned files
            if "Infected files" in line or "Scanned files" in line or "FOUND" in line:
                print_message(line)
            # Capture removed files
            if "Removed." in line:
                total_removed += 1
                removed_file = line.split(":")[0]  # Extract filename from the line
                removed_files.append(removed_file)
                print_message(f"Removed: {removed_file}")

        # Display the results
        if total_removed > 0:
            print_message(f"Total files removed: {total_removed}")
            print_message(f"Files removed: {', '.join(removed_files)}")
        else:
            print_message("No infected files were removed.")

    except Exception as e:
        print_message(f"Exception while running clamscan: {e}")

def get_disk_name():
    """Get the disk name that is not /dev/sda"""
    print_message("Getting hardware info...")
    hwinfo_output = run_command(["sudo", "hwinfo", "--short"])
    disks = re.findall(r"/dev/sd\w", hwinfo_output.stdout)
    for disk in disks:
        if disk != "/dev/sda":
            print_message(f"Found disk: {disk}")
            return disk
    print_message("No suitable disk found")
    return None

def check_and_create_mount_point():
    """Check if /mnt/usb exists, create if not"""
    if not os.path.exists("/mnt/usb"):
        run_command(["sudo", "mkdir", "/mnt/usb"])
        print_message("/mnt/usb folder created.")
    else:
        print_message("/mnt/usb folder already exists.")

def is_device_mounted(device):
    """Check if the device is already mounted"""
    mounts = run_command(["mount"]).stdout
    if device in mounts:
        print_message(f"{device} is already mounted.")
        return True
    return False

def mount_device(device):
    """Mount the device to /mnt/usb"""
    if not is_device_mounted(device):
        print_message(f"Mounting {device} to /mnt/usb...")
        run_command(["sudo", "mount", device, "/mnt/usb"])
        print_message(f"{device} mounted to /mnt/usb.")

def unmount_device(device):
    """Unmount the device"""
    print_message(f"Unmounting {device} from /mnt/usb...")
    run_command(["sudo", "umount", "/mnt/usb"])
    print_message(f"{device} unmounted.")

def download_eicar_test_file():
    """Download the EICAR test file to /mnt/usb"""
    print_message("Downloading the EICAR test virus...")
    run_command(["sudo", "wget", "-O", "/mnt/usb/eicar.com", "https://secure.eicar.org/eicar.com.txt"])
    print_message("EICAR test virus downloaded.")

def option_1_freshclam_update():
    """Option 1: Run freshclam database update"""
    update_freshclam()

def option_2_download_and_scan():
    """Option 2: Download EICAR test file and scan"""
    disk = get_disk_name()
    if not disk:
        print_message("No disk found to scan. Returning to main menu.")
        return

    # Check and create /mnt/usb folder
    check_and_create_mount_point()

    # Mount the device if not mounted
    mount_device(disk)

    # Download EICAR test file
    download_eicar_test_file()

    # Run clamscan and show only the relevant output
    run_clamscan_with_filtered_output()

    # Unmount the device
    unmount_device(disk)

def option_3_scan_usb():
    """Option 3: Run a scan of USB"""
    disk = get_disk_name()
    if not disk:
        print_message("No disk found to scan. Returning to main menu.")
        return

    # Check and create /mnt/usb folder
    check_and_create_mount_point()

    # Mount the device if not mounted
    mount_device(disk)

    # Run clamscan and show only the relevant output
    run_clamscan_with_filtered_output()

    # Unmount the device
    unmount_device(disk)

def option_4_scan_and_remove():
    """Option 4: Run a scan of USB and remove infected files"""
    disk = get_disk_name()
    if not disk:
        print_message("No disk found to scan. Returning to main menu.")
        return

    # Check and create /mnt/usb folder
    check_and_create_mount_point()

    # Mount the device if not mounted
    mount_device(disk)

    # Run clamscan and remove infected files, with file names listed
    run_clamscan_with_filtered_output(remove_infected=True)

    # Unmount the device
    unmount_device(disk)

def main_menu():
    """Display the main menu and handle user selection"""
    while True:
        print_header("Main Menu:")
        print_menu_option("[1] RUN freshclam database update (RECOMMENDED)", ERROR_COLOR)
        print_menu_option("[2] Download test VIRUS and run the test SCAN")
        print_menu_option("[3] Run the scan of USB")
        print_menu_option("[4] Run the scan of USB and REMOVE INFECTED")
        print_menu_option("[5] Exit")
        print_prompt("[+] Please choose an option: ")

        choice = input()

        if choice == "1":
            option_1_freshclam_update()
        elif choice == "2":
            option_2_download_and_scan()
        elif choice == "3":
            option_3_scan_usb()
        elif choice == "4":
            option_4_scan_and_remove()
        elif choice == "5":
            print_message("Exiting...")
            break
        else:
            print_message("Invalid option. Please try again.")

if __name__ == "__main__":
    # Ensure clamscan and hwinfo are installed and available
    hwinfo_installed = check_installation("hwinfo", ["hwinfo"])
    clamscan_installed = check_installation("clamscan", ["clamav", "clamav-daemon"])

    # Show the main menu
    main_menu()
