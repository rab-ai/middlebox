import matplotlib.pyplot as plt
import json

def read_values(filename):
    """Dosyadaki her satırı okuyup float değere çevirir.
       rtts.txt dosyasında JSON formatında değerler varsa da işlenir.
    """
    values = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                value = float(line)
            except ValueError:
                try:
                    value = float(json.loads(line))
                except Exception as e:
                    print(f"Error converting line '{line}': {e}")
                    continue
            values.append(value)
    return values

if __name__ == '__main__':
    delays = read_values("delays.txt")
    rtts = read_values("rtts.txt")
    
    if delays and rtts:
        plt.figure(figsize=(6, 4))
        
        plt.xlim(0, 0.01)
        
        plt.ylim(3, 5)
        
        plt.scatter(delays, rtts, color="red")
        
        for x, y in zip(delays, rtts):
            if 4 <= y <= 5:  
                plt.plot([x, x], [4, y], 'r--')  
                plt.plot([0, x], [y, y], 'r--') 
            
        plt.xlabel("Mean Random Delay (ms)")
        plt.ylabel("Average RTT for Ping Packets(ms)")
        plt.title("Mean Delay vs. Average RTT")
        plt.grid(True)
        
        for x, y in zip(delays, rtts):
            if 4 <= y <= 5: 
                plt.annotate(f"({x:.3f}, {y:.3f})", (x, y))
            
        plt.show()
    else:
        print("No data found in delays.txt or rtts.txt")