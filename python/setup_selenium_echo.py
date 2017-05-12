# YAML
import yaml

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
    parser.add_argument(
        '--configuration',
        default=os.path.join(os.getcwd(), 'instances.yml'),
        help='The path to the configuration file')
    arguments = parser.parse_args()

    return arguments

def create_security_group(ec2, all_groups, config, name, description, permissions, group_id=None):
    try:
        sg = next(iter(ec2.security_groups.filter(GroupNames=[name]).limit(1)))
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'InvalidGroup.NotFound':
            # The group doesn't exist, so we can make it
            vpc_id = list(ec2.vpcs.limit(1))[0].id

            sg = ec2.create_security_group(
                GroupName=name,
                Description=description,
                VpcId=vpc_id
            )

            # Go through the permissions and make sure that any sg id's are filled in
            # This may result in new sgs being created
            for rule in permissions['ingress']:
                if rule.get('CidrIp', None) == 'current':
                    rule['CidrIp'] = get_default_source_ip()
                elif rule.get('SourceSecurityGroupName', None) in all_groups:
                    # We're going to be using another security group as a valid connection source, make sure that group is created
                    other_group = all_groups[rule['SourceSecurityGroupName']]
                    create_security_group(ec2, all_groups, other_group, **other_group)
                    rule['SourceSecurityGroupName'] = other_group['name']

                sg.authorize_ingress(**rule)
        else:
            # There's a problem, but it's not that the group's not there
            raise
    
def main(arguments):
    ec2 = boto3.resource('ec2')
    with open(arguments.configuration) as config_file:
        config = yaml.load(config_file)

    # Create the security groups
    for typ, group_configuration in config['security groups'].items():
        create_security_group(
            ec2=ec2,
            all_groups=config['security groups'],
            config=group_configuration,
            **group_configuration)

    # Create VMs using vagrant
    v = vagrant.Vagrant(
        root=os.path.expanduser(arguments.vagrant_directory),
        quiet_stdout=False,
        quiet_stderr=False)
    v.up()

    # Make AMI's out of the instances, then delete the instances
    for instance in ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': list(set([info['ami'] for info in config['vm information'].values()]))}, {'Name': 'instance-state-name', 'Values': ['running']}]):
        img = instance.create_image(Name=next(tag['Value'] for tag in instance.tags if tag['Key'] == 'Name'))
        img.wait_until_exists(Filters=[{'Name': 'state', 'Values': ['available']}])
        instance.terminate()
        instance.wait_until_terminated()

if __name__=="__main__":
    main(parse_arguments())
