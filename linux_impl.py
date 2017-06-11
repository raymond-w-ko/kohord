import sys
import os
import evdev as e
from evdev import ecodes

import keyfilter


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


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
    keyfilter.kill_signal_handler()
    sys.exit(0)


def create_virtual_keyboard():
    global virtual_keyboard
    # accepts only KEY_* events by default, which is perfect
    virtual_keyboard = e.UInput(name="virtual uinput keyboard")


def hook_into_real_keyboard(keyboard_device):
    global keyboard
    keyboard = e.InputDevice(keyboard_device)
    keyboard.grab()


def translate_impl_to_event(event):
    input = {}
    key = ecodes.KEY[event.code][len("KEY_"):].lower()
    input["key"] = key

    if event.value == 0:
        input["state"] = "up"
    elif event.value == 1:
        input["state"] = "down"
    elif event.value == 2:
        input["state"] = "hold"
    return input


def translate_event_to_impl(input):
    sec = 0
    usec = 0
    type = ecodes.EV_KEY

    code = 255
    key = "KEY_" + input["key"].upper()
    code = ecodes.ecodes[key]

    value = None
    if input["state"] == "up":
        value = 0
    elif input["state"] == "down":
        value = 1
    elif input["state"] == "hold":
        value = 2

    event = e.events.InputEvent(sec, usec, type, code, value)
    return event


def event_sink(input_event):
    event = translate_event_to_impl(input_event)
    event = event
    virtual_keyboard.write(event.type, event.code, event.value)
    virtual_keyboard.syn()


def init(keyboard_device):
    global virtual_keyboard
    global keyboard
    if not os.path.exists(keyboard_device):
        eprint("keyboard /dev/input/eventN not found: %s" % (keyboard_device))
        return

    create_virtual_keyboard()
    hook_into_real_keyboard(keyboard_device)

    keyfilter.load_config_file()
    keyfilter.set_event_sink_and_start_producer_thread(event_sink)

    for event in keyboard.read_loop():
        if event.type == ecodes.EV_KEY:
            input_event = translate_impl_to_event(event)
            keyfilter.input_event(input_event)


def main(argv):
    print(sys.argv)
    if len(sys.argv) != 2:
        eprint("%s [keyboard /dev/input/eventN]" % (sys.argv[0]))
        sys.exit(0)
    keyboard_device = sys.argv[1]
    init(keyboard_device)
