#!/usr/bin/env python3

import platform
import sys
import signal

impl = None
if platform.system() == "Linux":
    import linux_impl
    impl = linux_impl


def kill_signal_handler(signal, frame):
    impl.kill_signal_handler(signal, frame)


def main():
    signal.signal(signal.SIGHUP, kill_signal_handler)
    signal.signal(signal.SIGINT, kill_signal_handler)
    signal.signal(signal.SIGTERM, kill_signal_handler)

    impl.main(sys.argv)


if __name__ == "__main__":
    main()
