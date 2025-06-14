#!/usr/bin/env python3

import random
import time
import subprocess

from sender import send_covert_message

def generate_random_string(length):
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def main():
    count = 200
    base_len = 60
    min_delay = 0.005
    max_delay = 0.2

    for i in range(count):
        msg_len = random.randint(1, 6)
        delay = round(random.uniform(min_delay, max_delay), 3)
        message = generate_random_string(msg_len)

        print(f"[{i+1}/{count}] Sending: '{message}' (delay={delay}s)")

        send_covert_message(
            message=message,
            base_len=base_len,
            delay=delay,
            host=None,      # .env'deki INSECURENET_HOST_IP kullanılır
            port=8888,
            fake_mode=False
        )

if __name__ == "__main__":
    main()
