#!/usr/bin/env python3
import argparse
import json
import sys
from pymongo import MongoClient
import RPi.GPIO as GPIO
import time

def getClaOptions():
	parser = argparse.ArgumentParser()
	parser.add_argument('-b', required=True, dest='messageBroker', help='IP address or named address of the message broker to connect to')
	parser.add_argument('-p', default='/', dest='virtualHost', help='Virtual host to connect to on the message broker. [Default: "/"]')
	parser.add_argument('-c', default='Guest:pass', help='Login credentials to use when connecting to the message broker. [-c login:password] [Default: Guest:pass]', dest='credentials')
	parser.add_argument('-k', required=True, dest='routingKey', help='Routing key to use when subscribing to the pi_utilization exchange on the message broker')
	return parser.parse_args()

def dbGetDocumentFromCollectionByPeaks(collection, field):
	splitFields = field.split('.')
	if len(splitFields) > 1:
		return collection.find_one(sort=[(field, -1)], projection={field: 1})[splitFields[0]][splitFields[1]][splitFields[2]], collection.find_one(sort=[(field, 1)], projection={field: 1})[splitFields[0]][splitFields[1]][splitFields[2]]
	elif len(splitFields) == 1:
		return collection.find_one(sort=[(field, -1)], projection={field: 1})[field], collection.find_one(sort=[(field, 1)], projection={field: 1})[field]

# TODO
def consumeFromQueue():
	fake_data = {'net': {'eth0': {'tx': 0, 'rx': 0}, 'wlan0': {'tx': 230, 'rx': 1201}, 'lo': {'tx': 0, 'rx': 0}}, 'cpu': 0.00497512437810943}
	return json.dumps(fake_data)

def printMonitorOutput(dbCollection, payload):
	cpuMax, cpuMin = dbGetDocumentFromCollectionByPeaks(dbCollection, 'cpu')

	print('Host:')
	print('cpu: %f [Hi: %f, Lo: %f]' % (payload['cpu'], cpuMax, cpuMin))

	for netInterfaceKey, val in payload['net'].items():
		rxMax, rxMin = dbGetDocumentFromCollectionByPeaks(dbCollection, 'net.%s.rx' % (netInterfaceKey))
		txMax, txMin = dbGetDocumentFromCollectionByPeaks(dbCollection, 'net.%s.tx' % (netInterfaceKey))
		print('%s: rx=%d B/s [Hi: %d B/s, Lo: %d B/s], tx=%d B/s [Hi: %d B/s, Lo: %d B/s]' % (netInterfaceKey, val['rx'], rxMax, rxMin, val['tx'], txMax, txMin))

def initGpio():
	GPIO.setmode(GPIO.BCM)

	GPIO.setup(18, GPIO.OUT) #Red
	GPIO.setup(23, GPIO.OUT) #Green
	GPIO.setup(24, GPIO.OUT) #Blue

	GPIO.output(18, GPIO.LOW)
	GPIO.output(23, GPIO.LOW)
	GPIO.output(24, GPIO.LOW)


def setLedColor(color):
	if color == 'r':
		GPIO.output(18, GPIO.HIGH)
		GPIO.output(23, GPIO.LOW)
		GPIO.output(24, GPIO.LOW)
	elif color == 'g':
		GPIO.output(18, GPIO.LOW)
		GPIO.output(23, GPIO.HIGH)
		GPIO.output(24, GPIO.LOW)
	elif color == 'y':	
		GPIO.output(18, GPIO.HIGH)
		GPIO.output(23, GPIO.HIGH)
		GPIO.output(24, GPIO.LOW)
	else:
		GPIO.output(18, GPIO.LOW)
		GPIO.output(23, GPIO.LOW)
		GPIO.output(24, GPIO.HIGH)

# TODO
def changeThresholdLed(currentCpuUtil):
	if currentCpuUtil < 0.25:
		setLedColor('g')
	elif currentCpuUtil < 0.50:
		setLedColor('y')
	else:
		setLedColor('r')

def main():
	try:
		# Setup
		initGpio()
		db = MongoClient().assignment2_db
		
		payload = json.loads(consumeFromQueue())
		db.utilData.insert(payload)
		changeThresholdLed(payload['cpu'])

		printMonitorOutput(db.utilData, payload)
		GPIO.cleanup()

	except KeyboardInterrupt:
		GPIO.cleanup()

if __name__ == "__main__":
	main()
