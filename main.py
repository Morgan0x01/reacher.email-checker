#!/usr/bin/env python3
# Reacher.email Checker (Multi Threaded)
import os
import sys
import modules.module as m
from rich.progress import track
from concurrent.futures import ThreadPoolExecutor, as_completed

cwd = os.getcwd()


def main() -> None:
    m.print_banner()
    m.create_dir()
    args = m.get_arguments()

    if not (os.path.exists(args.input) and os.path.isfile(args.input)):
        m.console.print(f'[red][-] ERROR: Input file doesn\'t exist[/]')
        m.exit_()

    else:
        with open(args.input, 'r', encoding='utf8') as input_file:

            email_addresses = m.get_valid_addresses(input_file.readlines())
            threads = 5 if args.threads is None or 1 > args.threads > 20 else args.threads

            with ThreadPoolExecutor(max_workers=threads) as executor:
                count = 0
                total = len(email_addresses)
                colors = {'safe': 'green', 'unknown': 'd yellow', 'risky': 'b yellow', 'invalid': 'red'}
                futures = (executor.submit(m.check, email_address, args) for email_address in email_addresses)

                if args.verbose:
                    for future in as_completed(futures):
                        email_address, status = future.result()
                        count += 1

                        m.console.print(
                            f"[{count}/{total}]\tEMAIL ADDRESS: {email_address}\tSTATUS: [{colors[status]}]"
                            "{status.upper()}[/]")
                        m.save(f'{cwd}\\CHECKED_EMAILS\\{status}.txt', email_address)
                else:
                    for future in track(as_completed(futures), total=total, description='Validating...'):
                        email_address, status = future.result()
                        m.save(f'{cwd}\\CHECKED_EMAILS\\{status}.txt', email_address)


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted, Exiting now...")
        sys.exit(1)
