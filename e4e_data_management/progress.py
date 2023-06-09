'''Provides progress tracking facilities
'''
from __future__ import annotations

import logging
from enum import Enum, auto
from pathlib import Path
from threading import Event
from typing import Callable, Dict, Iterable, Optional, Set, Union


class ProgressTrackerEvent(Enum):
    """Task Service Event
    """
    NEW = auto()
    UPDATE = auto()
    CLOSE = auto()
    CANCEL = auto()


class ProgressTrackerService:
    """Top level tracker facility
    """
    __instance: ProgressTrackerService = None
    EVENG_LOG_PRIORITIES = {
        ProgressTrackerEvent.NEW: logging.INFO,
        ProgressTrackerEvent.UPDATE: logging.DEBUG,
        ProgressTrackerEvent.CLOSE: logging.INFO,
        ProgressTrackerEvent.CANCEL: logging.WARN,
    }
    def __init__(self):
        self.__trackers: Dict[Path, Tracker] = {}
        self.__event_handlers: Dict[ProgressTrackerEvent, Set[int]] = {evt:set()
                                                                    for evt in ProgressTrackerEvent}
        self.__handlers: Dict[int, Callable[[Tracker], None]] = {}

    @property
    def __log(self) -> logging.Logger:
        return logging.getLogger('Progress Tracker')

    @classmethod
    def get_instance(cls) -> ProgressTrackerService:
        """Gets the singleton service instance

        Returns:
            ProgressTrackers: Progress Tracker Service
        """
        if not cls.__instance:
            cls.__instance = ProgressTrackerService()
        return cls.__instance

    def get_tracker(self, name: Union[Path, str], total: int = None) -> Tracker:
        """Gets the tracker by name

        Args:
            name (Union[Path, str]): Tracker tree identifier
            total (int, optional): Total value for the tracker.  Leave empty to get an existing
            tracker. Defaults to None.

        Raises:
            ValueError: Attempting to get a nonexisting Tracker

        Returns:
            Tracker: Tracker instance
        """
        name = Path(name)
        if name not in self.__trackers:
            if not total:
                raise ValueError('Tracker does not exist')
            self.__trackers[name] = Tracker(name, total)

        return self.__trackers[name]

    def register_handler(self, event: ProgressTrackerEvent, cb_: Callable[[Tracker], None]) -> int:
        """Registers the callbackhandler

        Args:
            event (ProgressTrackerEvent): Progress Tracker Event
            cb_ (Callable[[Tracker], None]): Callback handler

        Returns:
            int: Callback id
        """
        fn_id = id(cb_)
        self.__event_handlers[event].add(fn_id)
        self.__handlers[fn_id] = cb_

    def unregister_handler(self, handler_id: int) -> None:
        """Unregisters the specified handler

        Args:
            handler_id (int): Handler ID.  This can be obtained by `id(cb)`, where `cb` is the
            callback function.
        """
        for handler_list in self.__event_handlers.values():
            if handler_id in handler_list:
                handler_list.remove(handler_id)
        if handler_id in self.__handlers:
            self.__handlers.pop(handler_id)

    def execute_event(self, event: ProgressTrackerEvent, tracker: Tracker) -> None:
        """Executes the specified event handlers

        Args:
            event (ProgressTrackerEvent): Event to execute
            tracker (Tracker): Tracker causing this event
        """
        handler_list = self.__event_handlers[event]
        for handler_id in handler_list:
            self.__handlers[handler_id](tracker)
        self.__log.log(self.EVENG_LOG_PRIORITIES[event],
                       "%s %s",
                       event.name, tracker.name.as_posix())

    def close_tracker(self, tracker_name: Path) -> None:
        """Closes the specified tracker

        Args:
            tracker_name (Path): Name of tracker
        """
        tracker = self.__trackers.pop(tracker_name)
        self.execute_event(ProgressTrackerEvent.CLOSE, tracker)

    def wrap(self, iterable: Iterable, name: str) -> IterableTracker:
        """Creates an iterable tracker wrapping an interable

        Args:
            iterable (Iterable): Iterable to wrap
            name (str): Name of tracker

        Returns:
            IterableTracker: Trackable iterable
        """
        name = Path(name)
        tracker = IterableTracker(iterable, name)
        self.__trackers[name] = tracker
        return tracker

class TrackerInterrupt (KeyboardInterrupt):
    """Progress Tracker Interrupt
    """


class Tracker:
    """Progress Tracker
    """
    def __init__(self, name: Path, total: int) -> None:
        self.__name = Path(name)
        self.__total = total
        self.__idx = 0
        self.__msg: Optional[str] = None
        service = ProgressTrackerService.get_instance()
        service.execute_event(ProgressTrackerEvent.NEW, self)
        self.__cancel_event = Event()

    @property
    def name(self) -> Path:
        """Tree name of this Progress Tracker

        Returns:
            Path: Tree name
        """
        return self.__name

    @property
    def total(self) -> int:
        """Total iterations that this progress tracker is tracking

        Returns:
            int: Total iterations at completion
        """
        return self.__total

    @property
    def idx(self) -> int:
        """Current iteration

        Returns:
            int: Current iteration
        """
        return self.__idx

    @property
    def message(self) -> Optional[str]:
        """Optional iteration message.  This is reset every iteration

        Returns:
            Optional[str]: Optional iteration message
        """
        return self.__msg

    def update(self, idx: int, total: Optional[int] = None, msg: Optional[str] = None) -> None:
        """Manual update to progress

        Args:
            idx (int): Current iteration index
            total (Optional[int], optional): Updated total. Defaults to None.
            msg (Optional[str], optional): Optional iteration message. Defaults to None.

        Raises:
            TrackerInterrupt: Raised if the progress tracker has indicated that this task should be
            interrupted
        """
        if self.__cancel_event.is_set():
            raise TrackerInterrupt
        self.__idx = idx
        self.__msg = msg
        if total:
            self.__total = total
        service = ProgressTrackerService.get_instance()
        service.execute_event(ProgressTrackerEvent.UPDATE, self)

    def increment(self, msg: Optional[str] = None) -> None:
        """Increments the current progress

        Args:
            msg (Optional[str], optional): Optional iteration message. Defaults to None.

        Raises:
            TrackerInterrupt: Raised if the progress trackeer has indicated that this task should be
            interrupted
        """
        if self.__cancel_event.is_set():
            raise TrackerInterrupt
        self.__idx += 1
        self.__msg = msg
        service = ProgressTrackerService.get_instance()
        service.execute_event(ProgressTrackerEvent.UPDATE, self)

    def __enter__(self) -> Tracker:
        return self

    def __exit__(self, exc, exv, exp) -> None:
        self.close()

    def close(self):
        """Closes this progress tracker
        """
        service = ProgressTrackerService.get_instance()
        service.close_tracker(self.__name)

    def get_sub_trackere(self, name: Union[str, Path], total: int) -> Tracker:
        """Creates a nested tracker

        Args:
            name (Union[str, Path]): Child name
            total (int): Total iterations to be tracked

        Returns:
            Tracker: Nested tracker
        """
        service = ProgressTrackerService.get_instance()
        retval = service.get_tracker(name=self.__name.joinpath(name), total=total)
        return retval

    def cancel(self):
        """Causes the tracked progress to emit a TrackerInterrupt
        """
        self.__cancel_event.set()
        service = ProgressTrackerService.get_instance()
        service.execute_event(ProgressTrackerEvent.CANCEL, self)

class IterableTracker (Tracker, Iterable):
    """Iterable Tracker for wrapping iterables
    """
    def __init__(self, iterable: Iterable, name: Path) -> None:
        total = len(iterable)
        self.__iterable = iterable
        super().__init__(name, total)

    def __iter__(self):
        try:
            for obj in self.__iterable:
                self.increment()
                yield obj
        finally:
            self.close()
        return self
