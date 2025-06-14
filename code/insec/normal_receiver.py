"""
PS docker compose exec insec bash
root@1307206b6432:/code/insec# python3 normal_receiver.py  
with 
root@b6f513bfd544:/code/sec# python3 /code/sec/simple_udp_client_random.py --min-len 40 
--max-len 100 --min-delay 0.005 --max-delay 0.2 --count 200
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

def start_receiver(port=12345, output_file="features.csv"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    sock.settimeout(15)

    prev_time = None
    fieldnames = ["length", "inter_arrival", "entropy", "label"]

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        try:
            while True:
                data, addr = sock.recvfrom(4096)
                now = time.time()
                inter_arrival = now - prev_time if prev_time else 0
                prev_time = now

                length = len(data)
                entropy = calculate_entropy(data)
                label = "normal"

                writer.writerow({
                    "length": length,
                    "inter_arrival": round(inter_arrival, 5),
                    "entropy": round(entropy, 5),
                    "label": label
                })
                print(f"[RECV] len={length}  entropy={entropy:.2f}  ia={inter_arrival:.3f}  label={label}")
        except socket.timeout:
            print("[!] Timeout – listener stopped.")
        finally:
            sock.close()
            print(f"[✓] Features saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=12345)
    parser.add_argument('--output', type=str, default="features.csv",)
    args = parser.parse_args()

    start_receiver(port=args.port, output_file=args.output)
