from time import sleep as time_sleep
from time import time
from typing import Callable, Tuple
import math


def quantise_to(source_low: float, source_high: float,
                max_level: int, low_pad: float = 0.0, high_pad: float = 0.0) -> Callable[[float], int]:
    """
    Interpolation into a 0-n integer range, quantising the input value. Particularly useful when mapping
    an arbitrary level into an LED bar graph, mapping a float -1.0 to 1.0 into a motor control signal 0-255,
    or similar.

    :param source_low:
        Source value which should quantise to 0
    :param source_high:
        Source value which should quantise to [levels]
    :param max_level:
        Value of the highest level to which the input will be quantised. Including zero, this means there are
        max_level+1 buckets into which the input will be quantised. The output value will never exceed this, or
        be below zero.
    :param low_pad:
        Quantisation is performed using the floor() operator. This means that values which map to < 1
        will be quantised to zero. Sometimes you may want to have a very low threshold where almost all low
        values actually quantise to 1 rather than 0, leaving 0 to indicate 'no signal' or similar. This value
        is the lowest value the intermediate mapping will produce - if set to 1 you will only get a mapping to
        0 when the source input is at its very lowest value, lower values will reduce this effect. Defaults to 0
        for no padding, the lowest 1/(max_level+1) of values will quantise to zero.
    :param high_pad:
        Similar to low pad, but decreases the proportion of values which will result in a quantisation to the
        highest level rather than lowest. At 1.0 only values equal to source_high quantise to the highest value.
        Default to 0 for no padding, the top 1/(max_level+1) of values will quantise to the highest level
    :return:
        a function of source -> level configured to perform the requested quantisation
    """
    if low_pad > 1.0 or low_pad < 0:
        raise ValueError(f'low_pad must be between 0.0 and 1.0, was {low_pad}')
    if high_pad > 1.0 or high_pad < 0:
        raise ValueError(f'high_pad must be between 0.0 and 1.0, was {high_pad}')
    if max_level < 1:
        raise ValueError(f'number of quantisation levels must be greater than zero')
    i = interpolator(source_low=source_low, source_high=source_high,
                     dest_low=low_pad, dest_high=max_level + 1 - high_pad,
                     lock_range=True)

    return lambda value: min(max_level, math.floor(i(value)))


def tuple_interpolator(source_low: float, source_high: float,
                       dest_low: float = 0, dest_high: float = 1,
                       lock_range=False) -> Callable[[Tuple[float]], Tuple[float]]:
    """
    Convenience method to wrap an interpolator such that it interpolates all values in a
    tuple, returning a corresponding tuple of the same size with interpolated values. This
    can be used to handle interpolation for colours, vectors etc, provided the individual
    values within the tuple are all interpolated on the same basis, i.e. a tuple of 0-255
    which should be mapped to values in 0.0-1.0 or similar. It can't handle cases where the
    interpolation requirements are different for different elements within the tuple.

    :param source_low:
        See interpolator
    :param source_high:
        See interpolator
    :param dest_low:
        See interpolator
    :param dest_high:
        See interpolator
    :param lock_range:
        See interpolator
    :return:
        A function of source tuple to dest tuple such that all values in the source are interpolated
        to the corresponding value in the destination
    """
    i = interpolator(source_low, source_high, dest_low, dest_high, lock_range)
    return lambda t: tuple([i(value) for value in t])


def interpolator(source_low: float, source_high: float,
                 dest_low: float = 0, dest_high: float = 1,
                 lock_range=False) -> Callable[[float], float]:
    """
    General interpolation function factory

    :param source_low:
        Low input value
    :param source_high:
        High input value
    :param dest_low:
        Desired output value when the input is equal to source_low
    :param dest_high:
        Desired output value when the input is equal to source_high
    :param lock_range:
        If true (default) the output values will always be strictly constrained to the dest_high, dest_low range,
        if false then input values outside of source_low, source_high will result in output values beyond this
        constraint, acting as true linear interpolation.
    :return:
        a function of source->dest which applies the specified interpolation
    """
    if source_low > source_high:
        # Ensure that source_low is always numerically less than source_high
        return interpolator(source_high, source_low, dest_high, dest_low, lock_range)
    if source_low == source_high:
        raise ValueError(f'unable to create interpolator, source_low == source_high == {source_low}')

    source_range_inverse = 1 / (source_high - source_low)

    # If we're not locked then just use interpolation
    def inner_interpolator(value: float) -> float:
        i = (value - source_low) * source_range_inverse
        return i * dest_high + (1.0 - i) * dest_low

    # Otherwise return a version which clamps the interpolation value between 0 and 1
    def inner_locked_interpolator(value: float) -> float:
        i = max(0.0, min(1.0, (value - source_low) * source_range_inverse))
        return i * dest_high + (1.0 - i) * dest_low

    # Return a function from source -> dest
    return inner_locked_interpolator if lock_range else inner_interpolator


class IntervalCheck:
    """
    Utility class which can be used to run code within a polling loop at most once per n seconds. Set up an instance
    of this class with the minimum delay between invocations then enclose the guarded code in a construct such as
    if interval.should_run(): - this will manage the scheduling and ensure that the inner code will only be called if
    at least the specified amount of time has elapsed. As a shortcut you can also evaluate the instance itself, this
    calls should_run() and returns the result, but is somewhat less obvious.

    This class is particularly used to manage hardware where we may wish to include a hardware read or write in a fast
    polling loop such as the task manager, but where the hardware itself cannot usefully be written or read at that
    high rate.

    Instances of this class can also be used in 'with' clauses, i.e. 'with interval:' - this will sleep if required
    before running the gated code, then set the last run time to be the current time. This is not quite the same as
    just calling sleep() before running a code block, as it resets the time after the code has run, instead of after
    the sleep call has completed. Used in this mode therefore the interval is from the end of one code block to the
    start of the next, whereas normally it is from the start of one code block to the start of the next.
    """

    def __init__(self, interval):
        """
        Constructor

        :param float interval:
            The number of seconds that must pass between True values from the should_run() function
        """
        self.interval = interval
        self.last_time = None

    def should_run(self) -> bool:
        """
        Determines whether the necessary interval has elapsed. If it has, this returns True and updates the internal
        record of the last runtime to be 'now'. If the necessary time has not elapsed this returns False. This is also
        the truth value returned when evaluating the IntervalCheck itself as true or false.
        """
        now = time()
        if self.last_time is None or now - self.last_time > self.interval:
            self.last_time = now
            return True
        else:
            return False

    def __bool__(self) -> bool:
        return self.should_run()

    def sleep(self) -> None:
        """
        Sleep, if necessary, until the minimum interval has elapsed. If the last run time is not set this function will
        set it as a side effect, but will not sleep in this case. Calling sleep() repeatedly will therefore not sleep
        on the first invocation but will subsequently do so each time.
        """
        now = time()
        if self.last_time is None:
            self.last_time = now
            return
        elif now - self.last_time > self.interval:
            return
        else:
            remaining_interval = self.interval - (now - self.last_time)
            time_sleep(remaining_interval)
            self.last_time = now + remaining_interval

    def __enter__(self):
        self.sleep()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.last_time = time()
