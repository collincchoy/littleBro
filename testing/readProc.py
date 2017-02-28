#!/usr/bin/env python3
import time

def main():
	last_idle = last_total = 0
	startTime = time.time()
	while True:
		try:
			with open('/proc/stat') as f:
				fields = [float(column) for column in f.readline().strip().split()[1:]]
			idle, total = fields[3], sum(fields)
			idle_delta, total_delta = idle - last_idle, total - last_total
			last_idle, last_total = idle, total
			utilization = (1.0 - idle_delta / total_delta)
			print('%f' % utilization, end='\r')
			time.sleep ((100-(((time.time()*100) - (100*startTime))%100))/100)
		except KeyboardInterrupt:
			break

if __name__ == "__main__":
	main()
