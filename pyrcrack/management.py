#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import os
import subprocess
from contextlib import suppress
from . import Air, PATH, WrongArgument
from subprocess import DEVNULL, Popen


class Airmon(Air):
    """
        Airmon-ng object.

        It doubles as a context manager.
        So you can call it as

        ::

            wifi = Airmon().start('wlan0')
            Airmon('smoothie0').stop()
            Airmon('wlan0').check()

        or as

        ::
            with Airmon('wlan0') as f:
                print(f.interface)

    """

    def __init__(self, interface):
        """
            We need this to use the context manager.
            So I decided to make interface mandatory
        """
        self.interface = interface  #: Wireless interface
        super(self.__class__, self).__init__()

    def _do_action(self, what):
        """
            Execute airmon-ng with MON_PREFIX and PATH set.
        """
        env = {'PATH': PATH, 'MON_PREFIX': 'smoothie'}
        return subprocess.check_output(["airmon-ng", what,
                                        self.interface], env=env)

    def start(self):
        """
            Executes

            ::

                airmon-ng  start <WIFI>

            and replaces self.interface with the monitor interface.
        """
        ret = self._do_action('start')

        for asg in re.finditer(r'(.*) on (.*)\)', ret.decode()):
            self.interface = asg.group(2)
            return self.interface

    def stop(self):
        """
            Stops monitor mode on current interface
        """
        with suppress(subprocess.CalledProcessError):
            self._do_action('stop')


class Airdecap(Air):
    """
        Airdecap-ng object.
    """

    _allowed_arguments = (
        ('l', False),
        ('b', False),
        ('e', False),
    )

    _allowed_arguments_wep = (
        ('w', False),
    )

    _allowed_arguments_wpa = (
        ('p', False),
        ('k', False),
    )

    _allowed_attacks = (
        'wpa', 'wep'
    )

    def __init__(self, attack=False, file_=False, **kwargs):
        self.file_ = file_

        if attack not in self._allowed_attacks:
            raise WrongArgument

        self.attack = attack
        extra = tuple()
        with suppress(AttributeError):
            extra = getattr(self, "_allowed_arguments_{}".format(attack))
        self._allowed_arguments = self._allowed_arguments + \
            extra
        super(self.__class__, self).__init__(**kwargs)

    def start(self):
        """
            Executes airdecap-ng
        """
        params = self.flags + self.arguments
        line = ["airdecap-ng"] + params + [self.file_]
        self._proc = Popen(line, bufsize=0,
                           env={'PATH': os.environ['PATH']},
                           stderr=DEVNULL, stdin=DEVNULL, stdout=DEVNULL)
        os.system('stty sane')
        return self.result

    @property
    def result(self):
        """
            Returns the resulting file.
        """
        parts = self.file_.split('.')
        parts_ = parts[:-1]
        parts_.extend(["{}-dec.{}".format(parts[-2], parts[-1])])
        return '.'.join(parts_)
