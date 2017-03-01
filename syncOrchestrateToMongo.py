#!/usr/bin/python
# Use the Orchestrate porc client to migrate orchestrate collections to MongoDB
# Tested against Python 2.7.6, Orchestrate.io, and MongoDB 3.4.1
# Tested supporting libraries:  pymongo 3.4.0, porc 0.5.4


import sys
import netrc
import json

import porc
from porc import Client

from pymongo import MongoClient

# Set to one for potentially noisy logs
DEBUG = 0

# Using .netrc keeps keys and other private data out of repositories.  Read up on .netrc for the details
# Get authentication secrets
secrets = netrc.netrc()

# Set the right datacenter for the Orchestrate data
orcHost = 'api.ctl-uc1-a.orchestrate.io'
orcURI = 'https://' + orcHost + '/v0'
# Set Orchestrate Credentials
orcUser, orcAcct, orcKey = secrets.authenticators(orcHost)

if DEBUG == 1:
    sys.stdout.write("Connecting to Orchestrate with key = " + orcKey + "\n")

# Connect to Orchestrate and validate key/connection
oClient = Client(orcKey, orcURI)
oClient.ping().raise_for_status()
# Set the mongo endpoint.
mongoEndpoint = '192.168.0.1'
mongoPort = '27017'
mongoURI = "mongodb://" + mongoEndpoint + ":" + mongoPort

# Set Mongo Credentials
mongoUser, mongoAcct, mongoBasePass = secrets.authenticators(mongoEndpoint)
mongoPass = mongoBasePass.decode('base64').rstrip('\n')

if DEBUG == 1:
    sys.stdout.write("Connecting to " + mongoURI + " with user: " + mongoUser + "\n")
client = MongoClient(mongoURI)

# Specify the database to use
db = client.somedatabase

# Authenticate with that database
db.authenticate(mongoUser, mongoPass)

# Specify the collections to migrate
Collections = ['Collection1', 'Collection2', 'Collection3']
for collection in Collections:
    if DEBUG == 1:
        sys.stdout.write("Syncing collection: " + collection + "\n")
    data = oClient.list(collection).all()
    for record in data:
        jsonQuery = "{\"_id\":\"" + record['value']['id'] + "\"}"
        mongoQuery = json.loads(jsonQuery)
        update = record['value']
        update['_id'] = record['value']['id']
        if update['created'] is not None:
            update['created'] = DT.datetime.utcfromtimestamp(update['created']/1e3)
        result = db[collection].update(mongoQuery, update, upsert=True)
        if DEBUG == 1:
            if result['updatedExisting']:
                sys.stdout.write("Updated record for " + record['value']['id'] + "\n")
            if not result['updatedExisting']:
                sys.stdout.write("Inserted record with _id " + record['value']['id'] + "\n")