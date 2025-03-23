import subprocess
import json

def run_ping_via_docker(container="6cd607b43e2e", target="insec", count=20):
    docker_cmd = f"docker exec {container} ping -c {count} {target}"
    process = subprocess.Popen(
        docker_cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output, _ = process.communicate()
    
    rtt_values = []

    for line in output.splitlines():
        if "time=" in line:
            try:
                # Example: "64 bytes from insec (10.0.0.21): icmp_seq=4 ttl=64 time=4.66 ms"
                rtt = float(line.split("time=")[1].split(" ")[0])
                rtt_values.append(rtt)
            except (IndexError, ValueError):
                continue
    
    return rtt_values

if __name__ == "__main__":
    rtt_values = run_ping_via_docker()
    if rtt_values:
        average_rtt = sum(rtt_values) / len(rtt_values)
        print("RTT Values:", rtt_values)
        print(f"Average RTT: {average_rtt:.2f} ms")
        result = round(average_rtt, 2)
        with open("rtts.txt", "a") as f:
            f.write(json.dumps(result) + "\n")
    else:
        print("Ping output could not be parsed.")
        
    with open("stop_signal.txt", "w") as f:
        f.write("stop")
