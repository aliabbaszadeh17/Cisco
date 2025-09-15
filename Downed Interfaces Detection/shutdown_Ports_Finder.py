import csv
import maskpass
from netmiko import ConnectHandler
import re
from datetime import datetime


def get_device_info():
    """Prompt the user for device connection details (IP, username, password).

    Returns:
        dict: Device connection parameters for Netmiko
    """
    host = input("Enter the device IP address: ")
    username = input("Enter your username: ")
    password = maskpass.askpass(prompt="Enter your password:", mask="*")
    return {
        'device_type': 'cisco_ios',
        'host': host,
        'username': username,
        'password': password,
    }


def get_device_hostname(connection):
    """Retrieve the hostname from the device's running configuration.

    Args:
        connection (Netmiko): Established Netmiko connection

    Returns:
        str or None: Hostname if found, else None
    """
    output = connection.send_command("show running-config | include hostname")
    match = re.search(r"hostname\s+([\w.-]+)", output)
    if match:
        return match.group(1)
    else:
        return None


def find_down_interfaces(output):
    """Parse the `show ip int br` output to find interfaces that are down.

    Args:
        output (str): Output from `show ip int br`

    Returns:
        list: Interfaces that are down or administratively down (excluding VLAN interfaces)
    """
    down_interfaces = []
    for line in output.strip().split("\n")[1:]:
        columns = line.split()
        # Ensure we have enough columns to avoid index errors
        if len(columns) < 6:
            continue
        interface = columns[0]
        status = columns[4]
        protocol = columns[5]
        if "Vlan" not in interface and (status == "down" or status == "administratively") and protocol == "down":
            down_interfaces.append(interface)
    return down_interfaces


def parse_interface_output(output):
    """Parse `show int <interface>` output to extract last input and last output times.

    Args:
        output (str): Output from `show int <interface>`

    Returns:
        tuple: (last_input, last_output) values or (None, None) if not found
    """
    last_input_match = re.search(r"Last input (\S+),", output)
    last_output_match = re.search(r"output (\S+),", output)
    last_input = last_input_match.group(1) if last_input_match else None
    last_output = last_output_match.group(1) if last_output_match else None
    return last_input, last_output


def is_never_or_more_than_5w(time_str):
    """Check if a time string is either 'never' or more than 5 weeks.

    Args:
        time_str (str): Time string like 'never' or '5w'

    Returns:
        bool: True if 'never' or >=5 weeks, False otherwise
    """
    if time_str == "never":
        return True
    if time_str and "w" in time_str:
        try:
            weeks = int(time_str.split("w")[0])
            return weeks >= 5
        except ValueError:
            return False
    return False


# Main execution wrapped in a try/except to handle runtime errors gracefully
try:
    device = get_device_info()
    # Establish a connection to the device
    connection = ConnectHandler(**device)

    hostname = get_device_hostname(connection)
    if hostname is None:
        raise ValueError("Unable to retrieve device hostname")

    show_ip_int_br_output = connection.send_command("show ip int br")

    # Find down/unused interfaces
    down_interfaces = find_down_interfaces(show_ip_int_br_output)

    now = datetime.now()
    file_name = f"shutdown_ports_{hostname}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.csv"

    # Write results to a CSV file in the current directory
    with open(file_name, mode='w', newline='') as csvfile:
        fieldnames = ['interface_name', 'last_input', 'last_output']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for interface in down_interfaces:
            interface_output = connection.send_command(f"show int {interface}")
            last_input, last_output = parse_interface_output(interface_output)
            if is_never_or_more_than_5w(last_input) or is_never_or_more_than_5w(last_output):
                writer.writerow({'interface_name': interface, 'last_input': last_input, 'last_output': last_output})

    print(f"CSV file '{file_name}' successfully created in the current path.")

    connection.disconnect()

except Exception as e:
    print(f"An error occurred: {e}")
