import subprocess
import time
import statistics

base_lengths = [50 , 60]           
delays = [0.05, 0.1]            
messages = [                             
    "Hello",                           
    "This is a longer test message."
]
repeats = 10                          


results = []

for base in base_lengths:
    for delay in delays:
        for message in messages:
            times = []
            received_list = []

            print(f"\n[TEST] base_len={base}, delay={delay}s, message='{message}'")

            for i in range(repeats):
                print(f"  ➤ Test {i+1}/{repeats}")
                
                subprocess.run(["docker", "exec", "insec", "pkill", "-f", "receiver.py"])
                subprocess.run(["docker", "exec", "insec", "bash", "-c", "echo -n '' > /code/insec/received_messages.txt"])
                time.sleep(0.5)

                subprocess.Popen([
                    "docker", "exec", "-d", "insec",
                    "python3", "/code/insec/receiver.py",
                    "--base-len", str(base)
                ])
                time.sleep(1.0)

                start = time.time()
                subprocess.run([
                    "docker", "exec", "sec",
                    "python3", "/code/sec/sender.py",
                    "--msg", message,
                    "--base-len", str(base),
                    "--delay", str(delay)
                ])
                duration = time.time() - start
                times.append(duration)
                time.sleep(1.0)

                try:
                    output = subprocess.check_output([
                        "docker", "exec", "insec", "cat", "/code/insec/received_messages.txt"
                    ]).decode().strip()
                    lines = output.split("\n")
                    received = lines[-1] if lines else "ERROR"
                except:
                    received = "ERROR"

                received_list.append(received)

            avg_time = sum(times) / len(times)
            capacity_bps = (len(message) * 8) / avg_time
            try:
                std_dev = statistics.stdev(times)
                conf_interval = 1.96 * std_dev / (repeats ** 0.5)
                conf_str = f"±{conf_interval:.2f}"
            except:
                conf_str = "±NA"

            success_rate = received_list.count(message) / repeats * 100

            results.append((base, delay, message, avg_time, capacity_bps, conf_str, ";".join(received_list), f"{success_rate:.0f}%"))
            print(f"⏱ Avg: {avg_time:.2f}s | 📡 Capacity: {capacity_bps:.2f}bps | ✅ Success: {success_rate:.0f}%")

with open("benchmark_results.csv", "w") as f:
    f.write("base_len,delay,message,avg_time,capacity,conf_interval,received_list,success_rate\n")
    for r in results:
        f.write(",".join(map(str, r)) + "\n")
