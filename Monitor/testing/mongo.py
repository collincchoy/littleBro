#!/usr/bin/env python3
from pymongo import MongoClient

stats = {"net": {'lo': {'rx': 0, 'tx': 0}, 'wlan0': {'rx': 708, 'tx': 2}, 'eth0': {'rx': 0, 'tx':0}}, 'cpu': 0.9}

stats1 = {"net": {'lo': {'rx': 0, 'tx': 0}, 'wlan0': {'rx': 708, 'tx': 1250}, 'eth0': {'rx': 0, 'tx':0}}, 'cpu': 0.021}
stats2 = {"net": {'lo': {'rx': 0, 'tx': 0}, 'wlan0': {'rx': 708, 'tx': 1192}, 'eth0': {'rx': 0, 'tx':0}}, 'cpu': 0.231}
stats3 = {"net": {'lo': {'rx': 0, 'tx': 0}, 'wlan0': {'rx': 708, 'tx': 1192}, 'eth0': {'rx': 0, 'tx':0}}, 'cpu': 0.2071}

db = MongoClient().assignment2_db

db.utilData.insert(stats)
db.utilData.insert(stats1)
#db.utilData.insert(stats2)
#db.utilData.insert(stats3)

def dbGetMaxCpuDocument(collection):
	return collection.find_one(sort=[('cpu', -1)])

def dbGetMinCpuDocument(collection):
	return collection.find_one(sort=[('cpu', 1)])

print('Max CPU Doc: ', dbGetMaxCpuDocument(db.utilData))

print('Min CPU Doc: ', dbGetMinCpuDocument(db.utilData))
