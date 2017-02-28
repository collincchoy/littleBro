#!/usr/bin/env python3
import argparse
import json
import sys
from pymongo import MongoClient
from pymongo import errors
import RPi.GPIO as GPIO
import pika
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
		args = getClaOptions()
		initGpio()
		db = MongoClient() # Get Mongo client
		db = db.assignment2_db
		
		# Set up connection to RabbitMQ broker
		login, password = args.credentials.split(":")
		serverCredentials = pika.PlainCredentials(login, password)
		serverParameters = pika.ConnectionParameters(args.messageBroker, 5672, args.virtualHost, serverCredentials)
		try:
			serverConnection = pika.BlockingConnection(serverParameters)
		except (pika.exceptions.ProbableAuthenticationError, pika.exceptions.ProbableAccessDeniedError, pika.exceptions.ConnectionClosed) as e:
			GPIO.cleanup()
			if type(e) == pika.exceptions.ProbableAuthenticationError:
				print("Error: Invalid Username or Password. Exiting...")
			elif type(e) == pika.exceptions.ProbableAccessDeniedError:
				print("Error: Invalid virtual host name. Exiting...")
			else:
				print("Error: Bad IP address for MessageBroker. Exiting...")
			return
		serverChannel = serverConnection.channel()
		serverChannel.queue_declare(queue=args.routingKey)
		serverChannel.exchange_declare(exchange='pi_utilization', type='direct')
		serverChannel.queue_bind(exchange='pi_utilization', queue=args.routingKey)
		
		# Callback to be called on message consumption	
		def callback(serverChannel, method, properties, body):
			payload = json.loads(body.decode('utf-8'))
			db.utilData.insert(payload)
			changeThresholdLed(payload['cpu'])
			printMonitorOutput(db.utilData, payload)
		
		# Consume from the message queue
		serverChannel.basic_consume(callback, queue=args.routingKey)
		try: 
			serverChannel.start_consuming()
		except (pika.exceptions.ConnectionClosed, errors.ServerSelectionTimeoutError, errors.AutoReconnect) as e:
			GPIO.cleanup()
			if type(e) == pika.exceptions.ConnectionClosed:
				print("Error: RabbitMQ connection closed.  Exiting...")
			elif type(e) == errors.AutoReconnect:
				print("Error: Lost connection with MongoDB. Exiting...")
			else:
				print("Error: Cannot connect to MongoDB. Exiting...")
			return
		
		GPIO.cleanup()

	except KeyboardInterrupt:
		GPIO.cleanup()

if __name__ == "__main__":
	main()
