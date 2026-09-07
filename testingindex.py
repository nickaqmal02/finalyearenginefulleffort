import time

data = list(range(10_000_000))  # 10 million items

# METHOD 1: Manual counter
start = time.time()
total = 0
i = 0
for item in data:
    total += item * i
    i += 1
manual_time = time.time() - start

# METHOD 2: enumerate
start = time.time()
total = 0
for i, item in enumerate(data):
    total += item * i
enum_time = time.time() - start

print(f"Manual counter: {manual_time:.4f} seconds")


# Output example:
# Manual counter: 1.2345 seconds
# enumerate:      0.9876 seconds
# Speedup:
# 1.25x faster! 🚀
#
"""
hello
"""
