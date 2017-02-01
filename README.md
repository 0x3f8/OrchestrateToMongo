# Orchestrate To Mongo Sync Script

Being a user of [Orchestrate.io](https://orchestrate.io) was a pretty good bargain.  They maintained a decent nosql infrastructure and it was one less thing for me to worry about.

With the demise of Orchestrate.io being imminent I had to find somewhere else to port my data.  Granted, there are other options like [mlab](https://mlab.com/) and [AWS Dynamodb](https://aws.amazon.com/dynamodb/), but for my purpose I decided to get some experience with MongoDB.

The challenge was to write a script and essentially sync all my data from Orchestrate to MongoDB.  The script should be able to be run over and over, perhaps even on a cron job, to keep the Orchestrate data synced to MongoDB.

This repo contains the script I came up with.  I can't guarantee it'll work for you but in theory it should.  I'll point out what I think is important in the sections below.


## Step 1 - Versions and Supporting Libraries

So first off, I haven't tested this against Python3.  I also haven't optimized it very much.  My dataset is pretty small but from what I've read with python-bsonjs and other libraries, there may be some improvements that could be made if you have large dictionary objects.

Either way you'll need to get a couple of libraries installed to start with, **porc** and **pymongo**

As of the time of writing this my tested versions are

- **Python:** 2.7.6
- **MongoDB:** 3.4.1
- **pymongo:** 3.4.0
- **porc:** 0.5.4
- **netrc:** Standard Python Library (should be included)


You should be able to install the other dependencies with


```
$ sudo pip install pymongo
$ sudo pip install porc

```

## Step 2 - Configure the script

Next you'll want to clone repo (or just download the script) and configure it

```
git clone https://github.com/0x3f8/OrchestrateToMongo.git

```
Within the script you'll need to configure the following sections

### Set the Orchestrate Endpoint

The URI line is likely right, but you'll want to set *orcHost* to match your Orchestrate datacenter.  If you haven't already done so, you should generate and API key for your collections as well.

```
orcHost = 'api.ctl-uc1-a.orchestrate.io'
orcURI = 'https://' + orcHost + '/v0'
```

### Set the MongoDB Endpoint

The endpoint can be Fully Qualified Domain Name, local resolvable hostname, or IP address for your MongoDB instance.  I haven't tested against a sharded cluster so use with caution if you give that a try.

The port will be the port you configured for MongoDB as well.  The default is already given but you can change it if you are running on a different port.

If you haven't already done so, you should create a database in your MongoDB instance and set credentials for it.  There's a great [tutorial here](https://docs.mongodb.com/manual/core/authorization/)

If you're using the official MongoDB docker image you'll also need to mount a path for the data and for a custom entrypoint.sh to enable auth.


```
mongoEndpoint = '192.168.0.1'
mongoPort = '27017'
mongoURI = "mongodb://" + mongoEndpoint + ":" + mongoPort
```
### Set the MongoDB Database for the collections

e.g. if your database is called gadgets

```
db = client.gadgets
```

### Set the list of Collections you wish to migrate

This is a list of one or more Orchestrate collections you wish to populate into MongoDB.  The collection names in MongoDB will be mirrored exactly as they are in Orchestrate.

e.g. To sync the collection *foo* use

```
Collections = ['foo']
```

or to sync *foo* and *bar* do

```
Collections = ['foo', 'bar']
```

### Set your unique ID.

In the script you'll see the following reference

```
record['value']['id']
```

For my dataset this was a UUID that was generated for each record and was the same as what Orchestrate was using for the unique ID.  If you are using a unique ID in your key/value pairs you'll want to choose the field that matches.  If you don't have your own unique value, you have two choices.  You can used the values from Orchestrate which are at the record['key'] and record['ref'] references or you can simply insert the data and MongoDB will generate a unique value for you.

One caveat is that the Orchestrate record['key'] values are not unique due to their use of [Data Version History](https://orchestrate.io/docs/data-version-history).  My understanding is that with each record update the is a new object with the same key but a new *ref* and *reftime* key/value pairing.  Since I'm filtering my records by the unique key/value I've assigned in the record I believe I'm only pulling the latest data, but that remains to be tested.

### Configure the credentials

Finally you need to configure your credentials.  These will go in a file called *.netrc* that resides in the home folder of the user that will execute the script.  The file should only be owned by your user and set with permissions something like 0600.

To prevent shoulder surfing of passwords I base64 encoded the mongo user password.  Yeah, kinda lame and only prevents the lowliest of script kiddies from doing anything directly with it.

I'll leave how you base64 encode your password as an exercise for the reader, but if you do it at the terminal as your script you might want to clear it from history too.

A sample file follows

**Sample .netrc**

```
machine 192.168.0.1
	login  mongodbuser
	password UzNjcmV0UGFzcwo=

machine api.ctl-uc1-a.orchestrate.io
        login none
        password aabb8c20-38f3-4e41-a8e5-8bffdd7bbafa
```

#### Script Logic

The script operates as follows

1. Connect to Orchestrate
2. Connect to MongoDB
3. Authenticate to the specific MongoDB Database
4. Iterate through each collection and

- Creates the collection if needed
- Perform an update using the unique ID
- If the record doesn't exist, one will be created
