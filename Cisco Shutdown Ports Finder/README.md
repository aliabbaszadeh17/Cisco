# Cisco Shutdown Ports Finder


This directory contains a Python script that connects to a Cisco IOS device over SSH and identifies network interfaces that are either **down** or **administratively down** and have not seen traffic for at least five weeks. Qualifying interfaces are written to a CSV file for easy review.

## Features

- Utilizes **Netmiko** to establish an SSH connection to the Cisco device.
- Automatically retrieves the device hostname.
- Parses the output of `show ip int br` to locate interfaces that are down (excluding VLAN interfaces).
- For each candidate interface, extracts the `last input` and `last output` times from `show int <interface>`.
- Interfaces with `last input` or `last output` equal to `never` or greater than **5 weeks** are recorded to a timestamped CSV file.

## Requirements

Python 3.8 or higher is recommended. Install dependencies with pip:

```bash
pip install -r requirements.txt
```

Required packages:

- **netmiko** – SSH connections to Cisco IOS devices.
- **maskpass** – Securely prompts for the password without echoing.

## Usage

1. Clone this repository or download the `cisco` folder.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the script and follow the prompts:

   ```bash
   python shutdown_ports.py
   ```

   You will be asked to enter:
   - The IP address of the Cisco switch.
   - Your username.
   - Your password (input will be hidden).

4. After execution, a CSV file is created in the current working directory with a name like `shutdown_ports_<hostname>_<YYYY-MM-DD_HH-MM-SS>.csv`. This file lists interfaces that meet the criteria, along with their last input/output times.

## Example

```text
Enter the device IP address: 192.168.1.1
Enter your username: admin
Enter your password: *****
CSV file 'shutdown_ports_Switch1_2025-09-15_12-34-56.csv' successfully created in the current path.
```

## Notes

- VLAN interfaces are intentionally ignored because they are virtual and often have different operational characteristics.
- Time thresholds are based on the `last input` and `last output` fields displayed by the `show interface` command on Cisco IOS.
- Ensure that SSH access is enabled on the target device and that your credentials have the necessary privileges to run the commands used in this script.
