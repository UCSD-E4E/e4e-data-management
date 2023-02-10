'''Data Wrangler main logic
'''
import argparse


class DataWrangler:
    """Data Wrangler application logic
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
        description="Field Data Management Tool"
    )

    args = parser.parse_args()

    app = DataWrangler()

if __name__ == '__main__':
    cli()
