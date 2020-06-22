"""
Sampler that mesures performances.
"""

import time
import collections
import signal

class Sampler(object):
    """
    Written from https://nylas.com/blog/performance.
    """

    def __init__(self, interval=0.005):
        self.interval = interval
        self._started = None
        self._stack_counts = collections.defaultdict(int)

    def _sample(self, signum, frame):
        stack = []
        while frame is not None:
            formatted_frame = '{}({})'.format(
                frame.f_code.co_name,
                frame.f_globals.get('__name__')
            )
            stack.append(formatted_frame)
            frame = frame.f_back

        formatted_stack = ';'.join(reversed(stack))
        self._stack_counts[formatted_stack] += 1
        signal.setitimer(signal.ITIMER_VIRTUAL, self.interval, 0)

    def start(self):
        self._started = time.time()
        try:
            signal.signal(signal.SIGVTALRM, self._sample)
        except ValueError:
            raise ValueError('Can only sample on the main thread')
        signal.setitimer(signal.ITIMER_VIRTUAL, self.interval, 0)

    def output_stats(self):
        if self._started is None:
            return ''
        elapsed = time.time() - self._started
        lines = [
            'elapsed {}'.format(elapsed),
            'granularity {}'.format(self.interval),
        ]
        ordered_stacks = sorted(
            self._stack_counts.items(),
            key=lambda kv: kv[1],
            reverse=True
        )
        lines.extend(
            [
                '{} {}'.format(frame, count)
                for frame, count in ordered_stacks
            ]
        )
        return '\n'.join(lines) + '\n'

    def reset(self):
        self._started = time.time()
        self._stack_counts = collections.defaultdict(int)

