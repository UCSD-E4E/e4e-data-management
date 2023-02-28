'''E4E Data Management Core
'''
import sys
from typing import Callable, Dict, List

from e4e_data_management.initialization import init_dataset, init_mission
from e4e_data_management.core import DataManager

def print_help():
    """Prints the top level help
    """

def status(args: List[str]) -> None:
    """Prints the current status

    Args:
        args (List[str]): Arguments
    """
    if len(args) != 0:
        print_help()
        return
    print(DataManager().status())

def list_datasets(args: List[str]) -> None:
    """Lists the known datasets

    Args:
        args (List[str]): Arguments
    """
    if len(args) != 0:
        print_help()
        return
    for dataset in DataManager().list_datasets():
        print(dataset)

def prune_datasets(args: List[str]):
    """Prunes missing datasets

    Args:
        args (List[str]): Arguments
    """
    if len(args) != 0:
        print_help()
        return
    DataManager().prune()

def main():
    """Main function
    """
    command_map: Dict[str, Callable[[List[str]], None]] = {
        'init_dataset': init_dataset,
        'init_mission': init_mission,
        'status': status,
        'list': list_datasets,
        'config': None,
        'activate': None,
        'add': None,
        'commit': None,
        'duplicate': None,
        'validate': None,
        'push': None,
        'zip': None,
        'unzip': None,
        'prune': prune_datasets,
    }
    args = sys.argv
    if args[1] not in command_map:
        print_help()
        return
    app_fn = command_map[args[1]]
    app_fn(args[2:])

if __name__ == '__main__':
    main()