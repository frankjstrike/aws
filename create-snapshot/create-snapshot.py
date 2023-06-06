#!/bin/python3

import boto3
import argparse
import sys
from time import sleep

#====================================== Functions ======================================#

def check_snapshot_progress(snapshots, description, session):

    progress = ''

    ec2_client = session.client('ec2')
    ec2_resource = session.resource('ec2')

    # While list of snapshots is not empty
    while len(snapshots) > 0:

        for snapshot in snapshots:
            get_snapshot = ec2_client.describe_snapshots(
                Filters = [
                    {
                        'Name' : 'tag:MountPoint',
                        'Values' : [snapshot['DeviceName']]
                    },
                    {
                        'Name' : 'tag:Name',
                        'Values' : [snapshot['ServerName']]
                    },
                    {
                        'Name' : 'description',
                        'Values' : [description]
                    }
                ]
            )

            for i in get_snapshot['Snapshots']:
                if 'Progress' in i:
                    progress = i['Progress']

            if progress == '100%':
                print('\t> Snapshot for volume %s on %s has been completed!' % (snapshot['DeviceName'], snapshot['ServerName']))
                snapshots.remove(snapshot)
            else:
                print('\t> [%s on %s] Progress: %s' % (snapshot['DeviceName'], snapshot['ServerName'], progress))
        
        # Wait 10 seconds every time it checks on snapshots
        sleep(10)
    
    
 
#======================================== Main ========================================#

def main():
    
    parser = argparse.ArgumentParser(description="Purpose: Create snapshots of specified instance")

    parser.add_argument("--awskey", help="AWS Access Key ID")
    parser.add_argument("--awssecret", help="AWS Secret Key ID")
    parser.add_argument("-d", "--description", help="Snapshot's description (Typycally used for Tags)")
    parser.add_argument("-i", "--instances", nargs='+', default=[], help="AWS Instance(s) to create Snapshot for")

    # If ran without arguments, print help menu
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    # Parameters passed to script 
    awskey = args.awskey
    awssecret = args.awssecret
    description = args.description
    instances = args.instances

    print('\nInitializing Platform')

    # creates a boto3 session that will be used by various functions to make boto3 calls
    session = boto3.Session(
        region_name='us-east-1',
        aws_access_key_id = awskey,
        aws_secret_access_key = awssecret
    )

    ec2_client = session.client('ec2')
    ec2_resource = session.resource('ec2')

    # Create snapshot for every instance specified
    for instance in instances:
                
        volumes = []        

        print(f"\nGetting volumes for {instance}")
        
        get_volumes = ec2_client.describe_instance_attribute(
            InstanceId = instance, 
            Attribute='blockDeviceMapping'
        )

        # Get Volume ID and device block name and server name
        for volume in get_volumes['BlockDeviceMappings']:
            
            volume_info = ec2_client.describe_volumes(
                VolumeIds = [
                    volume['Ebs']['VolumeId']
                ]
            )

            device_name = volume['DeviceName']
            volume_id = volume['Ebs']['VolumeId']
            server_name = ''
            owner = ''
            data_classification = ''
            lifecycle = ''


            #Gather tags from volume
            for tag in volume_info['Volumes'][0]['Tags']:
                if 'Name' in tag['Key']:
                    server_name = tag['Value']
                if 'Owner' in tag['Key']:
                    owner = tag['Value']
                if 'data_classification' in tag['Key']:
                    data_classification = tag['Value']
                if 'Lifecycle' in tag['Key']:
                    lifecycle = tag['Value']

            
            volumes.append({'ServerName' : server_name, 'DeviceName' : device_name, 'VolumeID' : volume_id, 
                            'Owner' : owner, 'DataClassification' : data_classification, 'Lifecycle' : lifecycle})

        for volume in volumes:

            print('\t> Creating Snapshot for volume %s on %s' % (volume['DeviceName'], volume['ServerName']))

            ec2_resource.create_snapshot(
                Description = description,
                VolumeId = volume['VolumeID'],
                TagSpecifications = [
                    {
                        'ResourceType' : 'snapshot',
                        'Tags' : [
                            {
                                'Key' : 'MountPoint',
                                'Value' : volume['DeviceName']
                            },
                            {
                                'Key' : 'Name',
                                'Value' : volume['ServerName']
                            },
                            {
                                'Key' : 'Owner',
                                'Value' : volume['Owner']
                            },
                            {
                                'Key' : 'data_classification',
                                'Value' : volume['DataClassification']
                            },
                            {
                                'Key' : 'Lifecycle',
                                'Value' : volume['Lifecycle']
                            }
                        ]
                    }
                ]
            )
    
        print('\nSnapshot progress status for %s' % volume['ServerName'])

        check_snapshot_progress(volumes, description, session)
    
    print("\n****All Snapshots have been completed!****")
                      
if __name__ == "__main__":
    main()