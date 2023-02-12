'''Tests the data commit tool logic
'''
import pytest

from e4e_data_management.storage import StorageTool


def test_bad_validation(single_expedition):
    """Tests validation on un-prepped dataset

    Args:
        single_expedition (Path): Expedition dataset
    """
    app = StorageTool(single_expedition)

    # This is an incomplete expedition data structure, with no manifests
    # or metadata files
    with pytest.raises(Exception):
        app.validate()

def test_good_validation(single_validated_expedition):
    """Tests validation on prepped dataset

    Args:
        single_expedition (Path): Expedition dataset
    """
    app = StorageTool(single_validated_expedition)
    app.validate()
