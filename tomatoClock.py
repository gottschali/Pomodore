# -*- coding: utf-8 -*-
# Created: 3/8/2018
# Project : OneClock

from TomatoClock import TomatoClock
from anki.hooks import addHook


def start():
    if TomatoClock.HAS_SET_UP:
        return
    rr = TomatoClock.OneClockAddon()
    rr.perform_hooks(addHook)
    TomatoClock.HAS_SET_UP = True

addHook("profileLoaded", start)
