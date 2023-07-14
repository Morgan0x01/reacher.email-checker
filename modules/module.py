import os
import re
import sys
import json
import time
import argparse
import requests
import urllib.parse
from typing import Any
from threading import Lock
from rich.console import Console
from email_validator import validate_email, EmailNotValidError

console = Console()
lock = Lock()


def create_dir() -> None:
    folder_name = 'CHECKED_EMAILS'

    if os.path.isdir(folder_name):
        return

    try:
        os.mkdir('CHECKED_EMAILS')

    except OSError:
        console.print(f"[red][-] ERROR: Couldn't create directory {folder_name}[/]")
        sys.exit(1)


def print_banner():
    clear()
    with open('modules/banner.txt', 'r') as banner:
        banner_ = banner.read()
        console.print(banner_)
        print('\n' * 2)
        time.sleep(2)


def save(file_name: str, content: str) -> None:

    with lock:
        while True:
            try:
                with open(file_name, "a", encoding="utf-8") as output_file:
                    output_file.write(content + "\n")
                    break
            except (IOError, PermissionError) as error:
                continue


def exit_() -> None:
    console.print('[yellow][+] Hit enter to exit...')
    input()
    sys.exit(1)


def clear() -> None:
    if os.name == 'posix':
        os.system('clear')
    elif os.name == 'nt':
        os.system('cls')


def validate_email_address(email_address: str) -> bool:
    try:
        _ = validate_email(email_address, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def get_valid_addresses(lines):
    email_addresses = set(lines)
    email_addresses = set(map(lambda e: e.strip(), email_addresses))  # strip newline character
    email_addresses = set(filter(lambda e: validate_email_address(e), email_addresses))  # filter valid email addresses

    return email_addresses


def check(email_address, args) -> tuple[Any, str]:
    time.sleep(1)
    
    reacher_url = 'http://185.225.74.174:8080/v0/check_email'  # URL for reacher.email backend; format: http://127.0.0.1:8080/v0/check_email
    from_email = 'hello@affordable-autos.ddnss.eu'  # From mail for email Auth
    hello_name = 'affordable-autos.ddnss.eu'  # FQDN of reacher.email backend server

    data = {
        'to_email': email_address,
        'from_email': from_email,  # (optional) email to use in the `FROM` SMTP command, defaults to "user@example.org"
        'hello_name': hello_name,  # (optional) name to use in the `EHLO` SMTP command, defaults to "localhost"
        # 'proxy': {              # (optional) SOCK5 proxy to run the verification through, default is empty
        #     'host': proxy_host,
        #     'port': 1080,
        #     'username': '',
        #     'password': ''
        # },
        # 'smtp_port': 587          # (optional) SMTP port to do the email verification, defaults to 25
    }

    if args.from_mail:
        data['from_email'] = args.from_mail
    if args.ehlo:
        data['hello_name'] = args.ehlo

    if args.proxy_host and args.proxy_port:
        console.print(f'[yellow][!] Note: Proxy usage may result in unstable outcomes.[/]')
        data['proxy'] = {}
        data['proxy']['host'] = args.proxy_host
        data['proxy']['port'] = args.proxy_port
        if args.proxy_user and args.proxy_pass:
            data['proxy']['username'] = args.proxy_user
            data['proxy']['password'] = args.proxy_pass

    if args.smtp_port:
        console.print(f'[yellow][!] Note: SMTP port defaults to 25, change only if you know what you\'re doing.[/]')
        data['smtp_port'] = args.smtp_port

    response = requests.post(url=reacher_url, json=json.dumps(data))
    status = str(response.json()["is_reachable"])

    return email_address, status


def get_arguments():
    parser = argparse.ArgumentParser(description='Validate email addresses with a Hosted Reacher.email REST backend')
    parser.add_argument('-u', '--url', metavar='', dest='url',
                        help='URL for Reacher.email backend (e.g. http://127.0.0.1:8080/v0/check_email)')
    parser.add_argument('-i', '--input', metavar='', dest='input',
                        help='Input text file (containing email address(es))')
    parser.add_argument('-f', '--from', metavar='', dest='from_mail',
                        help='Email to use in the `FROM` SMTP command')
    parser.add_argument('-e', '--ehlo', metavar='', dest='ehlo',
                        help='Name to use in the `EHLO` SMTP command, defaults to "localhost"')
    parser.add_argument('-t', '--threads', metavar='', dest='threads', type=int, default=None,
                        help='Number of threads (default=5, MAX=20)')
    # parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Enable verbose output')

    parser.add_argument('-ph', '--proxy-host', metavar='', dest='proxy_host',
                        help='Proxy host (IP address/Domain name) Note: Proxy usage may result in unstable outcomes')
    parser.add_argument('-pp', '--proxy-port', metavar='', dest='proxy_port', type=int, help='Proxy port')
    parser.add_argument('-pu', '--proxy-user', metavar='', dest='proxy_user', help='Proxy user (Optional)')
    parser.add_argument('-pc', '--proxy-pass', metavar='', dest='proxy_pass', help='Proxy password (Optional)')

    parser.add_argument('-sp', '--smtp-port', metavar='', dest='smtp_port', type=int,
                        help='SMTP port to do the email verification, defaults to 25 (Optional)')

    args = parser.parse_args()

    if args.url and args.input:  # Check for Required fields
        # simple Reacher.email API url Validation
        p = urllib.parse.urlsplit(args.url)

        # Valid hostname | IP address regex
        valid_host = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)+([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$'
        valid = False

        if p.netloc != '' and ':' in p.netloc:
            host, port = p.netloc.split(':')

            # check URL format is correct
            if p.scheme == 'http' and re.search(valid_host, host) is not None and port in range(1, 65535):
                if p.path == '/v0/check_email':
                    valid = True

        if not valid:
            console.print(
                '[red][-] ERROR: please enter a valid URL format for --url flag[/] [white](e.g. '
                'http://127.0.0.1:8080/v0/check_email)[/]')
            exit_()

        return args

    else:
        if not args.url:
            console.print('[red][-] ERROR: --url is required.[/] [white](Use the --help flag to see usage info)[/]')
            exit_()
        elif not args.input:
            console.print('[red][-] ERROR: --input is required.[/] [white](Use the --help flag  to see usage info)[/]')
            exit_()
        elif not args.output:
            console.print('[red][-] ERROR: --output is required.[/] [white](Use the --help flag  to see usage info)[/]')
            exit_()
