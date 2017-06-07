#!/usr/bin/env python3

import os
import sys
import signal
import time

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

try:
    import evdev as e
    from evdev import ecodes
except:
    eprint("'python-evdev' not installed")

keyboard = None
virtual_keyboard = None

def kill_signal_handler(signal, frame):
    global virtual_keyboard
    global keyboard
    if virtual_keyboard is not None:
        virtual_keyboard.syn()
        virtual_keyboard.close()
        virtual_keyboard = None
    if keyboard is not None:
        try:
            keyboard.ungrab()
        except:
            # we may not have grabbed they keyboard...
            pass
        keyboard = None
    sys.exit(0)

def create_virtual_keyboard():
    global virtual_keyboard
    # accepts only KEY_* events by default, which is perfect
    virtual_keyboard = e.UInput(name="virtual uinput keyboard")

def hook_into_real_keyboard(keyboard_device):
    global keyboard
    keyboard = e.InputDevice(keyboard_device)
    keyboard.grab()

def main(keyboard_device):
    global virtual_keyboard
    global keyboard
    if not os.path.exists(keyboard_device):
        eprint("keyboard /dev/input/eventN not found: %s" % (keyboard_device))
        return

    signal.signal(signal.SIGHUP, kill_signal_handler);
    signal.signal(signal.SIGINT, kill_signal_handler);
    signal.signal(signal.SIGTERM, kill_signal_handler);

    create_virtual_keyboard()
    hook_into_real_keyboard(keyboard_device)

    for event in keyboard.read_loop():
        if event.type == ecodes.EV_KEY:
            print(type(event))
            print(e.categorize(event))
            print(repr(event))
            virtual_keyboard.write(ecodes.EV_KEY, event.code, event.value)
            virtual_keyboard.syn()

    kill_signal_handler(None, None)

if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) != 2:
        eprint("%s [keyboard /dev/input/eventN]" % (sys.argv[0]))
        sys.exit(0)
    keyboard_device = sys.argv[1]
    main(keyboard_device)
