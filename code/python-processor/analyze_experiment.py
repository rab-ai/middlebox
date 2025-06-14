# analyze_experiment.py

import csv
import math
from scipy import stats

# Read original sent messages
with open("mitigator_results/sender_log.csv", "r", encoding="utf-8", errors="replace") as f:
    sent_messages = [line.strip() for line in f.readlines()]

# Read received messages
received_messages = []
with open("mitigator_results/features_covert.csv", "r",encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        received_messages.append(row["decoded_message"])

# Accuracy comparison
total = min(len(sent_messages), len(received_messages))
success = 0
length_diffs = []

for i in range(total):
    original = sent_messages[i]
    decoded = received_messages[i]

    if original == decoded:
        success += 1

    length_diffs.append(abs(len(original) - len(decoded)))

accuracy = success / total
avg_length_diff = sum(length_diffs) / total

# Confidence interval for accuracy
conf = 0.95
z = stats.norm.ppf(1 - (1 - conf) / 2)
margin = z * math.sqrt((accuracy * (1 - accuracy)) / total)

print(f"✅ Total messages: {total}")
print(f"✅ Correctly received: {success}")
print(f"✅ Accuracy: {accuracy:.3f} ± {margin:.3f} (95% CI)")
print(f"📏 Avg. length difference: {avg_length_diff:.2f} chars")
