'''E4E Data Management Core
'''
import argparse
import sys
from typing import Callable, Dict, List

from e4e_data_management.initialization import init_dataset


def print_help():
    """Prints the top level help
    """

def main():
    """Main function
    """
    command_map: Dict[str, Callable[[List[str]], None]] = {
        'init_dataset': init_dataset,
        'init_mission': None,
        'config': None,
        'select': None,
        'add': None,
        'commit': None,
        'duplicate': None,
        'validate': None,
        'push': None,
        'zip': None,
        'unzip': None
    }
    args = sys.argv
    if args[1] not in command_map:
        print_help()
        return
    app_fn = command_map[args[1]]
    app_fn(args[2:])

if __name__ == '__main__':
    main()