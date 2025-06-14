
#!/usr/bin/env python3
import asyncio
import os
import joblib
import time
from scapy.all import Ether, IP, UDP
from nats.aio.client import Client as NATS
from math import log2
import pandas as pd

model = joblib.load("detector_model_entropy.pkl")
feature_cols = ["length", "inter_arrival", "entropy"]
last_packet_time = None 
def compute_entropy(payload_bytes):
    if not payload_bytes:
        return 0.0
    byte_counts = [0] * 256
    for b in payload_bytes:
        byte_counts[b] += 1
    probs = [count / len(payload_bytes) for count in byte_counts if count > 0]
    return -sum(p * log2(p) for p in probs)

async def run():
    global last_packet_time

    nc = NATS()
    nats_url = os.getenv("NATS_SURVEYOR_SERVERS", "nats://nats:4222")
    await nc.connect(nats_url)

    async def message_handler(msg):
        global last_packet_time

        subject = msg.subject
        data = msg.data
        packet = Ether(data)

        if not packet.haslayer(IP) or not packet.haslayer(UDP):
            await forward_packet(subject, data, nc)
            return

        now = time.time()
        inter_arrival = now - last_packet_time if last_packet_time is not None else 0.0
        last_packet_time = now

        udp_layer = packet[UDP]
        payload = bytes(udp_layer.payload) if udp_layer.payload else b""
        entropy = compute_entropy(payload)
        length = len(payload)

        X = pd.DataFrame([[length, inter_arrival, entropy]], columns=feature_cols)
        prediction = model.predict(X)[0]  # 0: normal, 1: covert
        print(f"[MITIGATOR][DEBUG] Features: len={length}, ent={entropy:.4f}, iat={inter_arrival:.4f}, prediction={prediction}")
        print(f"[DEBUG TYPE] prediction={prediction} type={type(prediction)}")
        if prediction == "covert":
            print(f"[MITIGATOR] 🚫 Covert packet blocked (len={length}, ent={round(entropy, 2)}, iat={round(inter_arrival, 4)})")
            return
        else:
            print(f"[MITIGATOR] ✅ Normal packet passed (len={length}, ent={round(entropy, 2)}, iat={round(inter_arrival, 4)})")
            await forward_packet(subject, data, nc)

    async def forward_packet(subject, data, nc):
        if subject == "inpktsec":
            await nc.publish("outpktinsec", data)
        else:
            await nc.publish("outpktsec", data)

    await nc.subscribe("inpktsec", cb=message_handler)
    await nc.subscribe("inpktinsec", cb=message_handler)
    print("[MITIGATOR] Subscribed to inpktsec and inpktinsec topics")

    try:
        while True:
            await asyncio.sleep(1)
            if os.path.exists("stop_signal.txt"):
                print("[MITIGATOR] Stop signal detected. Exiting.")
                os.remove("stop_signal.txt")
                break
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting.")
    finally:
        await nc.close()

if __name__ == "__main__":
    asyncio.run(run())
