#!/bin/python3

import boto3
import sys
import argparse
from paramiko import SSHClient, AutoAddPolicy
from os.path import normpath, basename
import os
from time import sleep
import time
import sys

def download_logs(instance_ip):

    log_paths = [
            "/var/log/wildfly/console.log",
            "/var/log/jboss/console.log",
            "/var/log/jboss-as/console.log",
            "/opt/jboss/standalone/log/server.log",
            "/opt/wildfly/standalone/log/server.log",
            "/opt/jboss/standalone/log/gc.log",
            "/opt/wildfly/standalone/log/gc.log",
            "/opt/wildfly/standalone/logs/service-audit.log",
            "/opt/jboss/standalone/logs/service-audit.log",
      		"/tmp/threaddumps.zip",
    ]

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy)
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh","known_hosts")))

    ssh.connect(instance_ip, username="centos", key_filename="./pemkey.pem") # Comment this line if running script locally
    # ssh.connect(instance_ip, username="centos") # Uncomment this line if running script locally
    
    # Install Pre-Requisites for Thread Dump
    print("Installing java developer tools...")
    stdin, stdout, stderr = ssh.exec_command('sudo yum -y install java-1.8.0-openjdk-devel')
    exit_status = stdout.channel.recv_exit_status()
    print("Installing zip utility...")
    stdin, stdout, stderr = ssh.exec_command('sudo yum -y install zip')
    exit_status = stdout.channel.recv_exit_status()

    # Grab PID of JBoss process
    stdin, stdout, stderr = ssh.exec_command('pgrep -f java | head -1')
    javaPID = (str(stdout.readlines()[0])).strip()
    exit_status = stdout.channel.recv_exit_status()
    print("JBoss PID:" + javaPID)

    # Perform histogram of java memory usage
    print("Exporting memory usage...")
    stdin, stdout, stderr = ssh.exec_command('sudo su -c "jmap -histo ' + javaPID + ' > /tmp/threaddump_mem_usage.txt" -s /bin/sh jboss')
    exit_status = stdout.channel.recv_exit_status()

    # Perform 5 thread dumps
    print("Exporting thread dump...")
    for dumpCount in range(5):
      stdin, stdout, stderr = ssh.exec_command('sudo su -c "jstack ' + javaPID + ' > /tmp/threaddump_' + str(dumpCount) + '.txt" -s /bin/sh jboss')
      exit_status = stdout.channel.recv_exit_status()
      time.sleep(10)

    # Zip the thread dumps for export
    print("Zipping results...")
    stdin, stdout, stderr = ssh.exec_command('sudo find /tmp -name "threaddump_*" 2>/dev/null | sudo zip /tmp/threaddumps.zip -@')
    exit_status = stdout.channel.recv_exit_status()

    sftp = ssh.open_sftp()

    for log in log_paths:
        try:
            # Check if file exists on remote server. Will get exception if doesnt exist causing to go to next log
            sftp.stat(log)
            
            # Get file name to add to local file when copied over
            file = basename(normpath(log))

            # Downloads file and renames it with the following format: {IPADDRESS}_{LOGTYPE}.log
            print(f"\t> Downloading [{file}] from [{instance_ip}] ")
            sftp.get(log, instance_ip + '_' + file)
        except OSError:
            pass

    # Close the sftp and ssh connection
    sftp.close()
    ssh.close()
    

def main():

    parser = argparse.ArgumentParser(description="Purpose: Detach specified instances from ASG")

    parser.add_argument("--awskey", help="AWS Access Key ID")
    parser.add_argument("--awssecret", help="AWS Secret Key ID")
    parser.add_argument("-i", "--instance", help="Instance to be removed from ASG")

    # If ran without arguments, print help menu
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    # Parameters passed to script 
    awskey = args.awskey
    awssecret = args.awssecret
    instance = args.instance

    print('\nInitializing Platform\n')

    # Creates a boto3 session that will be used by various functions to make boto3 calls
    session = boto3.Session(
        region_name='us-east-1',
        aws_access_key_id = awskey,
        aws_secret_access_key = awssecret
    )

    # Setup boto3 clients
    ec2_client = session.client("ec2")
    asg_client = session.client("autoscaling")
    elb_client = session.client("elbv2")
    
    print("Retrieving AutoScaling Group name and IP address for [%s]\n" % instance)
    
    try:
        # Uses tag from ec2 Instance to determine ASG name 
        instance_details = ec2_client.describe_instances(
            InstanceIds = [instance]
        )
    except Exception as e:
        print(e)
        sys.exit(1)

    asg = ''
    ip = ''
    
    for detail in instance_details['Reservations']:
        for i in detail['Instances']:
            
            for tag in i['Tags']:
                
                # Get ASG Name
                if 'aws:autoscaling:groupName' in tag['Key']:
                    asg = tag['Value']

                # Get OS of instance | Leaving this here for future updates to script (For Windows boxes)
                if tag['Key'].lower() == 'os':
                    instance_os = tag['Value']
            
            # Get Instance IP Address to get logs later
            for interface in i['NetworkInterfaces'][0]['PrivateIpAddresses']:
                ip = interface['PrivateIpAddress']
                        
    # Download logs
    print(f"Downloading logs from [{instance}]\n")
    download_logs(ip)
    
    print("\t> Detaching [%s] from [%s]\n" % (instance, asg))
    asg_client.detach_instances(
        InstanceIds = [instance],
        AutoScalingGroupName = asg,
        ShouldDecrementDesiredCapacity = False
    )

    ## Check if instance has been removed from ELB
    # Getting ELB's target group name
    asg_details = asg_client.describe_auto_scaling_groups(
        AutoScalingGroupNames = [asg]
    )

    elb_target_group_arn = ''

    for i in asg_details['AutoScalingGroups']:
        for elb_target in i['TargetGroupARNs']:
            elb_target_group_arn = elb_target

    instance_in_elb = True

    print("\nChecking if instance is still in Load Balancer\n")
    while instance_in_elb:
        target_health = elb_client.describe_target_health(
            TargetGroupArn = elb_target_group_arn
        )

        instances_in_target = []

        for target in target_health['TargetHealthDescriptions']:
            instances_in_target.append(target['Target']['Id'])

        if instance in instances_in_target:
            print("\t> Instance is still in Load balancer")
            sleep(30)
        else:
            print("\n\t> Instance has been removed from Load balancer. Proceeding with Termination")
            instance_in_elb = False

    # Terminates instance after confirming that it is no longer on ELB
    print(f"\nTerminating instance [{instance}]\n")
    ec2_client.terminate_instances(
        InstanceIds = [instance]
    )

    print('Done!\n ( Y )\n ( . .)\no(") (")\n')

if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- Completed in %s seconds ---" % (time.time() - start_time))