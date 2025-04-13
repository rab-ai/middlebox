# ------------------------------------------------------------------------------
# UDP Receiver — Network Routing Note:
# This script listens for UDP messages in the `insec` container.
# If `sec` and `insec` containers are on different macvlan networks,
# packets sent from `sec` will not reach `insec` unless routing is configured.
#
# You must enable routing through the `mitm` container as follows:
#
# 1. Enable IP forwarding:
#    docker exec mitm sysctl -w net.ipv4.ip_forward=1
#
# 2. Configure iptables to allow forwarding:
#    docker exec mitm iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT
#    docker exec mitm iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
#
# 3. Add routing rules to each container:
#    On `sec`:
#      ip route add 10.0.0.0/16 via 10.1.0.2
#
#    On `insec`:
#      ip route add 10.1.0.0/16 via 10.0.0.2
#
# Use `docker exec mitm ip a` to identify the correct gateway IPs.
# ------------------------------------------------------------------------------

import os
import socket
import argparse
import sys

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

def get_bit_group(length, length_to_bit_map):
    return length_to_bit_map.get(length, None)

def start_receiver(port=8888, base_len=60, verbose=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(f"[Receiver] Listening on UDP port {port}...")

    path = "received_messages.txt"
    if os.path.exists(path):
        with open(path, "w") as f:
            pass

    bit_to_length_map, length_to_bit_map = generate_bit_mappings(base_len)

    def decode_header(sock):
        header_bits = ""
        while len(header_bits) < 8:
            data, _ = sock.recvfrom(4096)
            length = len(data)
            bit = '0' if length == base_len else '1'
            header_bits += bit
        return int(header_bits, 2)

    message_length = decode_header(sock)
    print(f"[Receiver] Header received: expecting {message_length} characters")

    bit_buffer = ""
    message = ""
    expected_bits = message_length * 8

    while len(message) < message_length:
        data, _ = sock.recvfrom(4096)
        pkt_len = len(data)
        bits = get_bit_group(pkt_len, length_to_bit_map)

        if bits is None:
            print(f"[!] Unexpected packet length: {pkt_len}")
            continue

        bit_buffer += bits

        while len(bit_buffer) >= 8:
            byte = int(bit_buffer[:8], 2)
            char = chr(byte)
            message += char
            bit_buffer = bit_buffer[8:]
            print(f"[+] Decoded so far: {message}")

    with open(path, "a") as f:
        f.write(f"{message}\n")

    print(f"[\u2705] Full message received: {message}")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP covert channel receiver")
    parser.add_argument('--port', type=int, default=8888, help='Port to listen on')
    parser.add_argument('--base-len', type=int, default=60, help='Base payload length for decoding')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    start_receiver(
        port=args.port,
        base_len=args.base_len,
        verbose=args.verbose
    )
