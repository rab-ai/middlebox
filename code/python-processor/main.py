import asyncio
from nats.aio.client import Client as NATS
import os, random
from scapy.all import Ether

delays = []

async def run():
    nc = NATS()
    nats_url = os.getenv("NATS_SURVEYOR_SERVERS", "nats://nats:4222")
    await nc.connect(nats_url)

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data
        packet = Ether(data)
        print(f"[{subject}] Ethernet frame captured:")
        
        delay = random.expovariate(1 / 5e-6)
        delays.append(delay)
        print(f"Applying delay: {round(delay * 1000, 5)} ms")
        await asyncio.sleep(delay)
        if subject == "inpktsec":
            await nc.publish("outpktinsec", data)
        else:
            await nc.publish("outpktsec", data)
    
    await nc.subscribe("inpktsec", cb=message_handler)
    await nc.subscribe("inpktinsec", cb=message_handler)
    print("Subscribed to inpktsec and inpktinsec topics")
    
    try:
        while True:
            await asyncio.sleep(1)
            
            if os.path.exists("stop_signal.txt"):
                print("Stop signal detected. Exiting loop.")
                os.remove("stop_signal.txt")
                break
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected.")
    finally:
        print("Disconnecting...")
        await nc.close()
        if delays:
            mean_delay = sum(delays) / len(delays)
            with open("delays.txt", "a") as f:
                f.write(f"{round(mean_delay * 1000, 5)}\n")
            print(f"Mean Delay: {round(mean_delay * 1000, 5)} ms")
            
if __name__ == '__main__':
    asyncio.run(run())
