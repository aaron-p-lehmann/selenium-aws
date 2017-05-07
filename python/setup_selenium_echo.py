# Boto
import boto3
from botocore.exceptions import ClientError

# Vagrant
import vagrant

# Python
import socket
import argparse
import os
import os.path
import pprint

def get_default_source_ip():
    """
    The default source ip is the public IP of the local computer, if it can be found.  If it can't be found, the default is "0.0.0.0/0", completely open
    """
    from json import load
    from urllib2 import urlopen

    try:
        return load(urlopen('https://api.ipify.org/?format=json'))['ip'] + '/32'
    except:
        return '0.0.0.0/0'

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Set up an AWS environment for Selneium testing")
    parser.add_argument(
        '--source-ips',
        default=get_default_source_ip(),
        help='The ip or subnet from which connections are allowed')
    parser.add_argument(
        '--vagrant-directory',
        default=os.getcwd(),
        help='The directory where the Vagrantfile is')
    arguments = parser.parse_args()

    return arguments

def create_security_group(ec2, name, description, permissions):
    try:
        list(ec2.security_groups.filter(GroupNames=[name]).limit(1))
    except Exception as e:
        if e.response['Error']['Code'] == 'InvalidGroup.NotFound':
            # The group doesn't exist, so we can make it
            vpc_id = list(ec2.vpcs.limit(1))[0].id

            ec2.create_security_group(
                GroupName=name,
                Description=description,
                VpcId=vpc_id
            ).authorize_ingress(
                IpPermissions=permissions['ingress'])
        else:
            # There's a problem, but it's not that the group's not there
            raise
    else:
        # There already was a group by this name, so don't do anything
        pass
    
def main(arguments):
    ec2 = boto3.resource('ec2')

    # Create the security group for hub
    create_security_group(
        ec2=ec2,
        name='selenium hub SG',
        description='The network security for the selenium hub',
        permissions={
            'ingress': [
               {'IpProtocol': 'tcp',
                'ToPort': 4444,
                'FromPort': 4444,
                'IpRanges': [{'CidrIp': arguments.source_ips}]},
               {'IpProtocol': 'tcp',
                'ToPort': 22,
                'FromPort': 22,
                'IpRanges': [{'CidrIp': arguments.source_ips}]}]
        })

    # Create the security group for node
    create_security_group(
        ec2=ec2,
        name='selenium node SG',
        description='The network security for the selenium node',
        permissions={
            'ingress': [
               {'IpProtocol': 'tcp',
                'ToPort': 22,
                'FromPort': 22,
                'IpRanges': [{'CidrIp': arguments.source_ips}]},
               {'IpProtocol': 'tcp',
                'ToPort': 5555,
                'FromPort': 5555,
                'IpRanges': [{'CidrIp': arguments.source_ips}]},
               {'IpProtocol': 'tcp',
                'ToPort': 5900,
                'FromPort': 5900,
                'IpRanges': [{'CidrIp': arguments.source_ips}]}]
        })

    # Create the security group for standalone
    create_security_group(
        ec2=ec2,
        name='selenium standalone SG',
        description='The network security for the selenium standalone',
        permissions={
            'ingress': [
               {'IpProtocol': 'tcp',
                'ToPort': 22,
                'FromPort': 22,
                'IpRanges': [{'CidrIp': arguments.source_ips}]},
               {'IpProtocol': 'tcp',
                'ToPort': 4444,
                'FromPort': 4444,
                'IpRanges': [{'CidrIp': arguments.source_ips}]},
               {'IpProtocol': 'tcp',
                'ToPort': 5900,
                'FromPort': 5900,
                'IpRanges': [{'CidrIp': arguments.source_ips}]}]
        })

    # Create VMs using vagrant
    v = vagrant.Vagrant(
        root=os.path.expanduser(arguments.vagrant_directory),
        quiet_stdout=False,
        quiet_stderr=False)
    v.up()

    # Make AMI's out of the instances, then delete the instances
    for instance in ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': ['ami-41d48e24']}, {'Name': 'instance-state-name', 'Values': ['running']}]):
        img = instance.create_image(Name=next(tag['Value'] for tag in instance.tags if tag['Key'] == 'Name'))
        img.wait_until_exists(Filters=[{'Name': 'state', 'Values': ['available']}])
        instance.terminate()
        instance.wait_until_terminated()

if __name__=="__main__":
    main(parse_arguments())
