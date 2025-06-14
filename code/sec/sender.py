# ------------------------------------------------------------------------------
# Network Routing Note:
# This script sends UDP packets from the `sec` container to the `insec` container.
# However, both containers are connected to different macvlan networks (`routed` and `exnet`),
# and macvlan interfaces cannot communicate directly with each other.
#
# To enable communication, routing must go through the `mitm` (middlebox) container,
# which is connected to both networks.
#
# Follow these steps inside the Docker setup:
#
# 1. Enable IP forwarding in the mitm container:
#    docker exec mitm sysctl -w net.ipv4.ip_forward=1
#
# 2. Allow forwarding between interfaces:
#    docker exec mitm iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT
#    docker exec mitm iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
#
# 3. Add routing rules:
#    From `sec` container:
#      ip route add 10.0.0.0/16 via 10.1.0.2
#
#    From `insec` container:
#      ip route add 10.1.0.0/16 via 10.0.0.2
#
# Replace IPs with the actual IP addresses of the `mitm` container
# (check with: docker exec mitm ip a).
# ------------------------------------------------------------------------------

import os
import socket
import time
import argparse
import random

def generate_bit_mappings(base_len):
    bit_to_length_map = {}
    length_to_bit_map = {}
    current_length = base_len

    for i in range(2):
        bits = format(i, '01b')
        bit_to_length_map[bits] = current_length
        length_to_bit_map[current_length] = bits
        current_length += 1

    for i in range(4):
        bits = format(i, '02b')
        bit_to_length_map[bits] = current_length
        length_to_bit_map[current_length] = bits
        current_length += 1

    for i in range(8):
        bits = format(i, '03b')
        bit_to_length_map[bits] = current_length
        length_to_bit_map[current_length] = bits
        current_length += 1

    return bit_to_length_map, length_to_bit_map

def adaptive_bit_encode(message, bit_to_length_map):
    lengths = []
    bitstream = ''.join(format(ord(c), '08b') for c in message)
    idx = 0
    while idx < len(bitstream):
        for size in random.sample([1, 2, 3], 3):  # Try random order of sizes
            bit_chunk = bitstream[idx:idx + size].ljust(size, '0')
            if bit_chunk in bit_to_length_map:
                lengths.append((bit_chunk, bit_to_length_map[bit_chunk]))
                idx += size
                break
        else:
            lengths.append((bitstream[idx], bit_to_length_map[bitstream[idx]]))
            idx += 1
    return lengths

def send_header(length_in_chars, base_len, sock, host, port):
    bit_str = format(length_in_chars, '08b')
    print(f"[Sender] Header bits: {bit_str} (={length_in_chars})")
    for bit in bit_str:
        payload_len = base_len if bit == '0' else base_len + 1
        sock.sendto(b'A' * payload_len, (host, port))
        print(f"[Sender] Sent bit {bit} as length {payload_len}")
        time.sleep(0.05)

"""def send_covert_message(message, base_len=60, delay=0.1, host=None, port=8888):
    if not host:
        host = os.getenv('INSECURENET_HOST_IP', '10.0.0.21')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    send_header(len(message), base_len, sock, host, port)
    print(f"[Sender] Sending message: {message}")

    bit_to_length_map, _ = generate_bit_mappings(base_len)
    encoded = adaptive_bit_encode(message, bit_to_length_map)

    for bits, length in encoded:
        payload = b'A' * length
        sock.sendto(payload, (host, port))
        print(f"[Sender] Sent '{bits}' as length {length}")
        time.sleep(delay)

    sock.close()"""

def send_covert_message(message, base_len=60, delay=0.1, host=None, port=8888, fake_mode=False):
    if not host:
        host = os.getenv('INSECURENET_HOST_IP', '10.0.0.21')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if not fake_mode:
        send_header(len(message), base_len, sock, host, port)
        print(f"[Sender] Sending message: {message}")

        bit_to_length_map, _ = generate_bit_mappings(base_len)
        encoded = adaptive_bit_encode(message, bit_to_length_map)

        for bits, length in encoded:
            payload = b'A' * length
            sock.sendto(payload, (host, port))
            print(f"[Sender] Sent '{bits}' as length {length}")
            time.sleep(delay)
    else:
        print("[Sender] FAKE MODE ENABLED — sending random UDP packets with no encoding.")
        for _ in range(len(message) + 8):  # header + body kadar
            length = random.randint(base_len, base_len + 2)
            payload = b'A' * length
            sock.sendto(payload, (host, port))
            print(f"[Sender] Sent dummy payload with length {length}")
            time.sleep(delay)

    sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP covert channel sender")
    parser.add_argument('--msg', type=str, default="Hello", help='Message to send')
    parser.add_argument('--base-len', type=int, default=60, help='Base payload length')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between packets (seconds)')
    parser.add_argument('--port', type=int, default=8888, help='UDP port')
    parser.add_argument('--host', type=str, default=None, help='Destination IP')
    parser.add_argument('--count', type=int, default=1, help='Number of packets to send')

    args = parser.parse_args()

    send_covert_message(
        message=args.msg,
        base_len=args.base_len,
        delay=args.delay,
        host=args.host,
        port=args.port
    )