#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pynput import keyboard
from pynput.keyboard import Key

import random
import asyncio
import time
import signal
import functools

SHIFT_KEYS = (Key.shift, Key.shift_r)

colors = {
    'green': '\033[92m',
    'red': '\033[91m',
    'endc': '\033[0m'
}

def colorize(text, color):
    """ Colorize console output with terminal escape sequences """
    return f"{colors[color]}{text}{colors['endc']}"

class ShiftsReader:
    """ Transition class for integrating `pyinput` shift handling in asyncio """

    def __init__(self, loop):
        self.listener = None
        self._handler_future = None
        self._loop = loop  # loop for scheduling callback

    def _handle_press(self, key):
        if self._handler_future is not None and (key == Key.shift or key == Key.shift_r):
            self._loop.call_soon_threadsafe(self._handler_future.set_result, key)

    async def get_shift(self):
        """ Returns shift received from listener """
        self._handler_future = asyncio.Future()
        return await self._handler_future

    def start(self):
        self.listener = keyboard.Listener(on_press=self._handle_press)
        self.listener.start()

    def stop(self):
        self.listener.stop()


class ShiftTrainer:
    LEFT_SHIFT_MAP = ('^', '&', '*', '(', ')', '_', '+',
                      'Y', 'U', 'I', 'O', 'P', '{', '}', '|',
                      'H', 'J', 'K', 'L', ':', '"',
                      'N', 'M', '<', '>', '?')
    RIGHT_SHIFT_MAP = ('~', '!', '@', '#', '$', '%',
                       'Q', 'W', 'E', 'R', 'T',
                       'A', 'S', 'D', 'F', 'G',
                       'Z', 'X', 'C', 'V', 'B')

    def __init__(self):
        self.shifts_reader = None
        self.train_task = None

    @classmethod
    def _get_random_key(cls):
        shift_key = random.choice(SHIFT_KEYS)
        if shift_key == Key.shift:
            letter = random.choice(cls.LEFT_SHIFT_MAP)
        else:
            letter = random.choice(cls.RIGHT_SHIFT_MAP)
        return letter, shift_key

    async def _train_loop(self):
        t = time.time()
        valid = 0
        count = 0
        try:
            while True:
                check_key, check_shift = self._get_random_key()
                print(check_key)
                pressed_shift = await self.shifts_reader.get_shift()
                count += 1

                if pressed_shift == check_shift:
                    print(colorize('OK', 'green'))
                    valid += 1
                else:
                    print(colorize('False', 'red'))

        except asyncio.CancelledError:
            if count != 0:
                return (time.time() - t) / count, valid / count * 100
            else:
                return None

    async def train(self):
        self.shifts_reader = ShiftsReader(asyncio.get_event_loop())
        self.shifts_reader.start()
        self.train_task = asyncio.ensure_future(self._train_loop())
        result = await self.train_task

        if result is not None:
            print(f'Reaction time: {result[0]}\nValid percentage: {result[1]}')

    def stop(self):
        self.shifts_reader.stop()
        self.train_task.cancel()


async def main():
    trainer = ShiftTrainer()
    loop = asyncio.get_event_loop()

    for signame in {'SIGINT', 'SIGTERM'}:
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(trainer.stop))

    await trainer.train()


if __name__ == '__main__':
    asyncio.run(main())
