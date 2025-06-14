"""
PS docker compose exec insec bash
root@1307206b6432:/code/insec# python3 covert_receiver.py 
with
root@b6f513bfd544:/code/sec# python3 /code/sec/covert_sender_benchmark.py
"""
import socket
import csv
import time
import math
import argparse
import os

def calculate_entropy(data):
    if not data:
        return 0.0
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    total = len(data)
    entropy = -sum((count / total) * math.log2(count / total) for count in freq.values())
    return entropy

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

import socket
import csv
import time
import math
import argparse

def calculate_entropy(data):
    if not data:
        return 0.0
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    total = len(data)
    entropy = -sum((count / total) * math.log2(count / total) for count in freq.values())
    return entropy

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

def start_receiver(port=8888, base_len=60, output_file="features_covert.csv"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    sock.settimeout(15)
    print(f"[Receiver] Listening on port {port}...")

    fieldnames = ["avg_length", "avg_inter_arrival", "avg_entropy", "label", "decoded_message"]
    bit_to_length_map, length_to_bit_map = generate_bit_mappings(base_len)

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        prev_time = None
        while True:
            try:
                # --- Header decoding ---
                header_bits = ""
                lengths = []
                inter_arrivals = []
                entropies = []

                while len(header_bits) < 8:
                    data, _ = sock.recvfrom(4096)
                    now = time.time()
                    inter_arrival = now - prev_time if prev_time else 0
                    prev_time = now

                    pkt_len = len(data)
                    entropy = calculate_entropy(data)

                    lengths.append(pkt_len)
                    inter_arrivals.append(inter_arrival)
                    entropies.append(entropy)

                    bit = '0' if pkt_len == base_len else '1'
                    header_bits += bit

                msg_len = int(header_bits, 2)
                print(f"[✓] Header received, expecting {msg_len} chars")

                # --- Message decoding ---
                bit_buffer = ""
                message = ""

                while len(message) < msg_len:
                    data, _ = sock.recvfrom(4096)
                    now = time.time()
                    inter_arrival = now - prev_time if prev_time else 0
                    prev_time = now

                    pkt_len = len(data)
                    entropy = calculate_entropy(data)

                    bits = get_bit_group(pkt_len, length_to_bit_map)
                    if bits is None:
                        print(f"[!] Unexpected length: {pkt_len}")
                        continue

                    lengths.append(pkt_len)
                    inter_arrivals.append(inter_arrival)
                    entropies.append(entropy)

                    bit_buffer += bits
                    while len(bit_buffer) >= 8 and len(message) < msg_len:
                        byte = int(bit_buffer[:8], 2)
                        char = chr(byte)
                        message += char
                        bit_buffer = bit_buffer[8:]

                print(f"[✓] Message decoded: {message}")

                writer.writerow({
                    "avg_length": round(sum(lengths) / len(lengths), 2),
                    "avg_inter_arrival": round(sum(inter_arrivals) / len(inter_arrivals), 5),
                    "avg_entropy": round(sum(entropies) / len(entropies), 5),
                    "label": "covert",
                    "decoded_message": message
                })

            except socket.timeout:
                print("[!] Receiver timeout — done listening.")
                break

    sock.close()
    print(f"[✓] Features saved to {output_file}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8888)
    parser.add_argument('--base-len', type=int, default=60)
    parser.add_argument('--output', type=str, default="features_covert.csv")
    args = parser.parse_args()

    start_receiver(port=args.port, base_len=args.base_len, output_file=args.output)
