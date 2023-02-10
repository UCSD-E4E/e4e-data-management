'''Storage Commit Tool main logic
'''
import argparse


class StorageTool:
    """Storage Tool application logic
    """
    def __init__(self):
        pass

def gui():
    """GUI Entry Point
    """

def cli():
    """CLI Entry Point
    """
    parser = argparse.ArgumentParser(
        description="Expedition Data Commit Tool"
    )

    args = parser.parse_args()

    app = StorageTool()

if __name__ == '__main__':
    cli()
