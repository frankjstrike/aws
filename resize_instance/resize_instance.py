#!/bin/python3

import logging
import time
import argparse
import sys
import boto3
from botocore.exceptions import ClientError

def create_session(awskey, secretkey):
    # creates a boto3 session that will be used by various functions to make boto3 calls
    session = boto3.Session(
        region_name='us-east-1',
        aws_access_key_id=awskey,
        aws_secret_access_key=secretkey
    )
    return session

def get_logger():
    """setup logging"""
    logging.basicConfig(stream = sys.stdout, level=logging.INFO)
    logger = logging.getLogger("Default")
    return logger

def stop_start_instance(action, ec2_client, instance):

    if action.lower() == "start":
        
        logger.info(f"> Starting instance: {instance}\n")
        try:
            ec2_client.start_instances(
                InstanceIds = [instance]
            )
        except ClientError as e:
            logger.error(f'Error starting instance {instance}: {e}\n Exiting script now')
            sys.exit()

    elif action.lower() == "stop":
        logger.info(f"> Stopping instance: {instance}\n")
        try:
            ec2_client.stop_instances(
                InstanceIds = [instance]
            )
        except ClientError as e:
            logger.error(f'Error stopping instance {instance}: {e}\n Exiting script now')
            sys.exit()

    else:
        raise Exception(f"> Unrecognized action: {action}\n Exiting script now")

def wait_for_instance(ec2_resource, action, instance):

    logger.info(f"> Waiting for instance to have status: {action}")

    try:
        instance_status = ec2_resource.Instance(instance)
            
        if action.lower() == "stopped":
            while not instance_status.state['Name'] == "stopped":
                logger.info(f"> {instance} state is: {instance_status.state['Name']}")
                time.sleep(10)

                instance_status = ec2_resource.Instance(instance)

            logger.info(f"> {instance} has been stopped!\n")

        elif action.lower() == "running":
            while not instance_status.state['Name'] == "running":
                logger.info(f"> {instance} state is: {instance_status.state['Name']}")
                time.sleep(10)

                instance_status = ec2_resource.Instance(instance)
            logger.info(f"> {instance} is running!\n")

    except ClientError as e:
            logger.error(f"> Unable to get {instance}'s status. Reason : {e}\n Exiting script now")
            sys.exit()

def change_instance_type(ec2_client, instance, size):
    
    logger.info(f"> Changing instance type of {instance} to {size}\n")

    try:
        ec2_client.modify_instance_attribute(
            InstanceId= instance,
            InstanceType = {
                "Value" : size
            }
        )
    except ClientError as e:
            logger.error(f"> Error trying to change Instance Type. Reason : {e}\n Exiting script now")
            sys.exit()

def get_parameters():
    parser = argparse.ArgumentParser(description="Purpose: Resize instances on AWS")
    parser.add_argument("--awskey", help="AWS Access Key ID", required=True)
    parser.add_argument("--awssecret", help="AWS Secret Key ID", required=True)
    parser.add_argument("-i", "--instance", help="Instance ID of node that is being resized", required=True)
    parser.add_argument("-s", "--size", help="Size of instance that it is being resized to", required=True)

    """If ran without arguments, print help menu"""
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    return args

def main():
    """setup our parameters"""
    args = get_parameters()

    """Parameters passed to script"""
    awskey = args.awskey
    secretkey = args.awssecret
    instance = args.instance
    size = args.size

    session = create_session(awskey, secretkey)
    ec2_client = session.client('ec2')
    ec2_resource = session.resource('ec2')

    try:
        """Stop the session prior to resize"""
        stop_start_instance("stop", ec2_client, instance)

        """Wait for instance to stop"""
        wait_for_instance(ec2_resource, "stopped", instance)

        """Change size of instance"""
        change_instance_type(ec2_client, instance, size)

        """Start the session prior to resize"""
        stop_start_instance("start", ec2_client, instance)

        """Wait for instance to become available"""
        wait_for_instance(ec2_resource, "running", instance)

        logger.info(f"> Instance [{instance}] successfully changed to [{size}]")

    except Exception as e:
        logger.error(f'> Something went wrong. Reason: {e}')

if __name__ == '__main__':
    start_time = time.time()    
    """setup logging"""
    logger = get_logger()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))