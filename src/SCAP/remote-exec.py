import argparse
import winrm
import paramiko
import wmi
import os

def run_winrm(host: str, username: str, password: str, command: str) -> None:
    session = winrm.Session(f'http://{host}:5985/wsman', auth=(username, password))
    result = session.run_cmd(command)
    print(result.std_out.decode())
    print(result.std_err.decode())

def run_ssh(host: str, username: str, credential: str, command: str) -> None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if os.path.exists(credential):
        client.connect(host, username=username, key_filename=credential)
    else:
        client.connect(host, username=username, password=credential)
    stdin, stdout, stderr = client.exec_command(command)
    print(stdout.read().decode())
    print(stderr.read().decode())
    client.close()

def run_wmi(host: str, username: str, password: str, command: str) -> None:
    conn = wmi.WMI(host, user=username, password=password)
    process_startup = conn.Win32_ProcessStartup.new()
    process_id, result = conn.Win32_Process.Create(CommandLine=command, ProcessStartupInformation=process_startup)
    print(f'Process ID: {process_id}, Result: {result}')

def main() -> None:
    parser = argparse.ArgumentParser(description='Send commands to Windows via various methods.')
    parser.add_argument('method', choices=['winrm', 'ssh', 'wmi'], help='Method to use for sending the command')
    parser.add_argument('host', help='Target host')
    parser.add_argument('username', help='Username for authentication')
    parser.add_argument('credential', help='Password (or ssh key path) for authentication')
    parser.add_argument('command', help='Command to execute')

    args = parser.parse_args()

    if args.method == 'winrm':
        run_winrm(args.host, args.username, args.credential, args.command)
    elif args.method == 'ssh':
        run_ssh(args.host, args.username, args.credential, args.command)
    elif args.method == 'wmi':
        run_wmi(args.host, args.username, args.credential, args.command)

if __name__ == '__main__':
    main()
