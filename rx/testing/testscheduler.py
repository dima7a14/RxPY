from typing import Callable, Any

from rx.core import Observable, ObservableBase, Disposable
from rx.concurrency import VirtualTimeScheduler

from .coldobservable import ColdObservable
from .hotobservable import HotObservable
from .mockobserver import MockObserver
from .reactivetest import ReactiveTest


class TestScheduler(VirtualTimeScheduler):
    """Test time scheduler used for testing applications and libraries
    built using Reactive Extensions. All time, both absolute and relative is
    specified as integer ticks"""

    __test__ = False

    def schedule_absolute(self, duetime: int, action: Callable, state: Any = None) -> Disposable:
        """Schedules an action to be executed at the specified virtual
        time.

        Keyword arguments:
        duetime -- Absolute virtual time at which to execute the
            action.
        action -- Action to be executed.
        state -- State passed to the action to be executed.

        Returns disposable object used to cancel the scheduled action
            (best effort).
        """

        duetime = duetime if isinstance(duetime, int) else self.to_relative(duetime)
        return super(TestScheduler, self).schedule_absolute(duetime, action, state)

    @staticmethod
    def add(absolute, relative):
        """Adds a relative virtual time to an absolute virtual time value"""

        return absolute + relative

    def start(self, create=None, created=None, subscribed=None, disposed=None) -> MockObserver:
        """Starts the test scheduler and uses the specified virtual times to
        invoke the factory function, subscribe to the resulting sequence, and
        dispose the subscription.

        Keyword arguments:
        :param types.FunctionType create: Factory method to create an
            observable sequence.
        :param int created: Virtual time at which to invoke the factory to
            create an observable sequence.
        :param int subscribed: Virtual time at which to subscribe to the
            created observable sequence.
        :param int disposed: Virtual time at which to dispose the subscription.

        :returns: Observer with timestamped recordings of notification messages
        that were received during the virtual time window when the subscription
        to the source sequence was active.
        :rtype: MockObserver
        """

        # Defaults
        create = create or Observable.empty
        created = created or ReactiveTest.created
        subscribed = subscribed or ReactiveTest.subscribed
        disposed = disposed or ReactiveTest.disposed

        observer = self.create_observer()
        subscription = [None]
        source = [None]

        def action_create(scheduler, state):
            """Called at create time. Defaults to 100"""
            source[0] = create()
            return Disposable.empty()
        self.schedule_absolute(created, action_create)

        def action_subscribe(scheduler, state):
            """Called at subscribe time. Defaults to 200"""
            subscription[0] = source[0].subscribe(observer, scheduler)
            return Disposable.empty()
        self.schedule_absolute(subscribed, action_subscribe)

        def action_dispose(scheduler, state):
            """Called at dispose time. Defaults to 1000"""
            subscription[0].dispose()
            return Disposable.empty()
        self.schedule_absolute(disposed, action_dispose)

        super().start()
        return observer

    def create_hot_observable(self, *args) -> ObservableBase:
        """Creates a hot observable using the specified timestamped
        notification messages either as a list or by multiple arguments.

        Keyword arguments:
        messages -- Notifications to surface through the created sequence at
            their specified absolute virtual times.

        Returns hot observable sequence that can be used to assert the timing
        of subscriptions and notifications.
        """

        if args and isinstance(args[0], list):
            messages = args[0]
        else:
            messages = list(args)
        return HotObservable(self, messages)

    def create_cold_observable(self, *args) -> ObservableBase:
        """Creates a cold observable using the specified timestamped
        notification messages either as an array or arguments.

        Keyword arguments:
        :param list[Notification] args: Notifications to surface through the
            created sequence at their specified virtual time offsets from the
            sequence subscription time.

        :returns: Cold observable sequence that can be used to assert the
            timing of subscriptions and notifications.
        :rtype: Observable
        """

        if args and isinstance(args[0], list):
            messages = args[0]
        else:
            messages = list(args)
        return ColdObservable(self, messages)

    def create_observer(self) -> MockObserver:
        """Creates an observer that records received notification messages and
        timestamps those. Return an Observer that can be used to assert the
        timing of received notifications.

        :returns: Observer
        :rtype: MockObserver
        """

        return MockObserver(self)
