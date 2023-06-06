# create-snapshot.py
-----------------

## Script Function
-----------------
This script will create snapshots of all volumes in a specified AWS instance

## Parameters
-----------------
*  -h, --help | show this help message and exit
*  --awskey AWSKEY | AWS Access Key ID
*  --awssecret AWSSECRET | AWS Secret Key ID
*  -d DESCRIPTION, --description DESCRIPTION | Snapshot's description (Typycally used for Tags)
*  -i INSTANCES [INSTANCES ...], --instances INSTANCES [INSTANCES ...] | AWS Instance(s) to create Snapshot for

## Calling Script Example
-----------------
usage: create-snapshot.py [-h] [--awskey AWSKEY] [--awssecret AWSSECRET] [-d DESCRIPTION] [-i INSTANCES [INSTANCES ...]]

* Create Snapshots for a single instance
```bash
./create-snapshot.py --awskey $AWSKEY --awssecret $AWSSECRET -d "DESCRIPTION" -i i-0e9549756596de29f
```

* Create Snapshots for a multiple instances
```bash
./create-snapshot.py --awskey $AWSKEY --awssecret $AWSSECRET -d "DESCRIPTION" -i i-0e954975659983478f i-048069f0e7f373d33 i-028347e12356e256
```