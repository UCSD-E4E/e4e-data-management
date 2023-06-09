'''Test the progress tracker system
'''
from typing import Dict, Tuple
from unittest.mock import Mock

from e4e_data_management.progress import (ProgressTrackerEvent,
                                          ProgressTrackerService, Tracker)

ProgressServiceFixture = Tuple[ProgressTrackerService, Dict[ProgressTrackerEvent, Mock]]
def test_basic_icrements(progress_tracker_service: ProgressServiceFixture):
    """Tests basic increments

    Args:
        progress_tracker_service (ProgressServiceFixture): Progress Service Fixture
    """
    service, handlers = progress_tracker_service
    with service.get_tracker('test_loop', 100) as loop1:
        assert isinstance(loop1, Tracker)
        assert loop1.total == 100
        assert loop1.idx == 0
        assert loop1.message is None
        handlers[ProgressTrackerEvent.NEW].assert_called_once_with(loop1)
        handlers[ProgressTrackerEvent.NEW].reset_mock()

        loop1.update(idx = 1)
        handlers[ProgressTrackerEvent.UPDATE].assert_called_once_with(loop1)
        assert loop1.idx == 1
        assert loop1.total == 100
        assert loop1.message is None
        handlers[ProgressTrackerEvent.UPDATE].reset_mock()

        loop1.increment()
        handlers[ProgressTrackerEvent.UPDATE].assert_called_once_with(loop1)
        assert loop1.idx == 2
        assert loop1.total == 100
        assert loop1.message is None

    handlers[ProgressTrackerEvent.CLOSE].assert_called_once()

def test_loop(progress_tracker_service: ProgressServiceFixture):
    """Tests usage in a basic loop

    Args:
        progress_tracker_service (ProgressServiceFixture): Progress Tracker Service Fixture
    """
    service, handlers = progress_tracker_service
    with service.get_tracker('loop1', 100) as loop1:
        for _ in range(100):
            loop1.increment()
    assert handlers[ProgressTrackerEvent.UPDATE].call_count == 100
    assert handlers[ProgressTrackerEvent.NEW].call_count == 1
    assert handlers[ProgressTrackerEvent.CLOSE].call_count == 1
    assert handlers[ProgressTrackerEvent.CANCEL].call_count == 0

def test_iterator(progress_tracker_service: ProgressServiceFixture):
    """Tests usage over a range object

    Args:
        progress_tracker_service (ProgressServiceFixture): Progress Tracker Service Fixture
    """
    service, handlers = progress_tracker_service
    for _ in service.wrap(range(100), name='loop1'):
        pass
    assert handlers[ProgressTrackerEvent.UPDATE].call_count == 100
    assert handlers[ProgressTrackerEvent.NEW].call_count == 1
    assert handlers[ProgressTrackerEvent.CLOSE].call_count == 1
    assert handlers[ProgressTrackerEvent.CANCEL].call_count == 0

def test_list(progress_tracker_service: ProgressServiceFixture):
    """Tests usage over a Collection

    Args:
        progress_tracker_service (ProgressServiceFixture): Progress Tracker Service Fixture
    """
    service, handlers = progress_tracker_service
    array = [idx for idx in range(200)]
    for _ in service.wrap(array, name='loop2'):
        pass
    assert handlers[ProgressTrackerEvent.UPDATE].call_count == 200
    assert handlers[ProgressTrackerEvent.NEW].call_count == 1
    assert handlers[ProgressTrackerEvent.CLOSE].call_count == 1
    assert handlers[ProgressTrackerEvent.CANCEL].call_count == 0
