#!/usr/bin/env python3
import time
import json
import argparse
import pika

def getClaOptions():
	parser = argparse.ArgumentParser()
	parser.add_argument('-b', required=True, dest='messageBroker', help='IP address or named address of the message broker to connect to')
	parser.add_argument('-p', default='/', dest='virtualHost', help='Virtual host to connect to on the message broker. [Default: "/"]')
	parser.add_argument('-c', default='Guest:pass', help='Login credentials to use when connecting to the message broker. [-c login:password] [Default: Guest:pass]', dest='credentials')
	parser.add_argument('-k', required=True, dest='routingKey', help='Routing key to use when publishing messages to the message broker')
	return parser.parse_args()

def getUtil(last_idle, last_total):
	with open('/proc/stat') as f:
			fields = [float(column) for column in f.readline().strip().split()[1:]]
	idle, total = fields[3], sum(fields)
	idle_delta, total_delta = idle - last_idle, total - last_total
	#last_idle, last_total = idle, total
	utilization = (1.0 - idle_delta / total_delta)
	return utilization, idle, total

def readNetDev(procNetDev):
	# remove table headers
	procNetDev.readline()
	procNetDev.readline()

	ntwrkInterfaceData = procNetDev.read()
	ntwrkInterfaceData = ntwrkInterfaceData.split('\n')

	ntwrkInterfaceData = filter(lambda x: len(x) > 10, ntwrkInterfaceData)

	netStatTotals = {interface[0][0:-1]:{'rx':int(interface[1]), 'tx':int(interface[9])} for interface in map(lambda x: x.split(), ntwrkInterfaceData)}

	procNetDev.seek(0,0)

	return netStatTotals

def calcNetworkThroughput(currentStats, lastStats):
	delta = {key: ({'rx': val['rx']-lastStats[key]['rx'], 'tx': val['tx']-lastStats[key]['tx']} if key in lastStats else {'rx': 0, 'tx': 0}) for key, val in currentStats.items()}

	return delta

def main():
	args = getClaOptions()

	# Initial Reads
	procNetDev = open("/proc/net/dev", "r")
	with open('/proc/stat') as f:
		fields = [float(column) for column in f.readline().strip().split()[1:]]
	last_idle, last_total = fields[3], sum(fields)
	last_netStats = readNetDev(procNetDev)

	startTime = time.time()

	# Set up connection to send data to repository RabbitMQ queue
	login, password = args.credentials.split(":")
	serverCredentials = pika.PlainCredentials(login, password)
	serverParameters = pika.ConnectionParameters(args.messageBroker, 5672, args.virtualHost, serverCredentials)
	serverConnection = pika.BlockingConnection(serverParameters)
	serverChannel = serverConnection.channel()
	serverChannel.queue_declare(queue=args.routingKey)
	serverChannel.exchange_declare(exchange='pi_utilization', type='direct')
	serverChannel.queue_bind(exchange='pi_utilization', queue=args.routingKey)
	while True:
		try:
			# Do every second
			time.sleep ((100-(((time.time()*100) - (100*startTime))%100))/100)

			# Read proc/stat for cpu utilization
			util, last_idle, last_total = getUtil(last_idle, last_total)
			
			# Read proc/net/dev for network throughput
			netStats = readNetDev(procNetDev)
			netStats_delta = calcNetworkThroughput(netStats, last_netStats)
			last_netStats = netStats

			# Serialize as JSON
			package = json.dumps({'net': netStats_delta, 'cpu': util})
			serverChannel.basic_publish(exchange='pi_utilization', routing_key=args.routingKey, body=package)
		except KeyboardInterrupt:
			break
	procNetDev.close()

if __name__ == "__main__":
	main()
