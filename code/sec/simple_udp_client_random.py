#!/usr/bin/env python3
"""
cd ~/Desktop/middle-box-v2/middlebox
docker compose exec sec bash
cd /code/sec

# Rastgele normal UDP trafiği üret
python3 simple_udp_client_random.py \
  --min-len   40 --max-len   100 \
  --min-delay 0.005 --max-delay 0.2 \
  --count     1000

exit

"""
import socket
import time
import argparse
import random
import os
def main():
    p = argparse.ArgumentParser(
        description="Randomize edilmiş normal UDP trafik jeneratörü"
    )
    p.add_argument("--min-len",   type=int,   default=50,
                   help="Payload uzunluğu için alt sınır (bayt)")
    p.add_argument("--max-len",   type=int,   default=80,
                   help="Payload uzunluğu için üst sınır (bayt)")
    p.add_argument("--min-delay", type=float, default=0.01,
                   help="Delay için alt sınır (saniye)")
    p.add_argument("--max-delay", type=float, default=0.1,
                   help="Delay için üst sınır (saniye)")
    p.add_argument("--count",     type=int,   default=200,
                   help="Gönderilecek toplam paket sayısı")
    args = p.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    import os
    target_host = os.getenv("INSECURENET_HOST_IP", "insec")
    target = (target_host, 12345)

    for i in range(args.count):
        payload_len = random.randint(args.min_len, args.max_len)
        delay       = random.uniform(args.min_delay, args.max_delay)

        payload = os.urandom(payload_len)
        sock.sendto(payload, target)
        print(f"[{i+1}/{args.count}] len={payload_len}, delay={delay:.3f}s")
        time.sleep(delay)

if __name__ == "__main__":
    main()
