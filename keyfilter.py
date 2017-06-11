import sys
import os
import re
import threading
from queue import Queue
from pprint import pprint

event_sink = None
output_queue = Queue()
key_buffer = []

subsitution_table = {}
modifer_key_set = set()
modifer_key_set.add("leftctrl")
modifer_key_set.add("rightctrl")
modifer_key_set.add("leftalt")
modifer_key_set.add("rightalt")


def clean_spaces(x):
    return re.sub(r"\s+", " ", x)


def kill_signal_handler():
    global output_queue
    output_queue.put("exit")


def output_loop():
    global output_queue
    while True:
        input_event = output_queue.get()
        if input_event == "exit":
            return
        event_sink(input_event)


def set_event_sink_and_start_producer_thread(_sink):
    global event_sink
    event_sink = _sink
    t = threading.Thread(target=output_loop)
    t.start()


def apply_substitutions():
    global output_queue
    global key_buffer
    global modifer_key_set
    global subsitution_table

    pattern = []

    for event in key_buffer:
        key = event["key"]
        state = event["state"]
        if state != "down":
            continue
        pattern.append(key)
    pattern = tuple(sorted(pattern))
    if pattern not in subsitution_table:
        for event in key_buffer:
            output_queue.put(event)
    else:
        substitution = subsitution_table[pattern]
        for key in substitution:
            event = {"key": key, "state": "down"}
            output_queue.put(event)
            event = {"key": key, "state": "up"}
            output_queue.put(event)
    del key_buffer[:]


def input_event(input_event):
    global output_queue
    global key_buffer
    global modifer_key_set
    state = input_event["state"]

    # no repeating keys for now
    if state == "hold":
        return

    # modifier keys get immediate output priority, cannot be chorded for
    # example, I hold down Ctrl while doing Ctrl+C and Ctrl+V and not let go
    if input_event["key"] in modifer_key_set:
        output_queue.put(input_event)
        return

    key_buffer.append(input_event)

    charges = {}
    for event in key_buffer:
        key = event["key"]
        state = event["state"]
        if key not in charges:
            charges[key] = 0

        if state == "down":
            charges[key] += 1
        elif state == "up":
            charges[key] -= 1
    total_charge = 0
    for key, charge in charges.items():
        total_charge += charge

    if total_charge == 0:
        apply_substitutions()


def load_config_file(path=None):
    if not path:
        path = os.path.join(os.path.dirname(__file__), "raymond.kohord")
    with open(path, "r") as f:
        lines = f.readlines()
        lines = map(lambda x: x.strip(), lines)
        lines = filter(lambda x: x, lines)
        lines = filter(lambda x: not x.startswith("#"), lines)
        lines = list(lines)
        num_entries = len(lines) // 2
        if num_entries % 2 != 0:
            print(".kohord config file malformed")
            sys.exit(1)
        for i in range(num_entries):
            lhs = clean_spaces(lines[i * 2 + 0])
            rhs = clean_spaces(lines[i * 2 + 1])
            pattern = tuple(sorted(lhs.split(" ")))
            sub = rhs.split(" ")
            if pattern in subsitution_table:
                print(".kohord file contains duplicated pattern")
                sys.exit(1)
            subsitution_table[pattern] = sub
    pprint(subsitution_table)
