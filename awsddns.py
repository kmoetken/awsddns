import requests
import json
import boto3
import os
import sys
import logging
import argparse
from time import sleep

def get_public_ip():

    url = 'https://api.ipify.org'

    params = {'format': 'json'}

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return False, None

    return True, response.json()['ip']

def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="Enable debugging")
    parser.add_argument("--domain", required=True, help="Domain Name")
    parser.add_argument("--zoneid", required=True, help="Route53 Domain ZoneId")
    parser.add_argument("--ttl", default=300, help="Time to Live (TTL) in seconds for DNS record (default: 300 seconds)")
    parser.add_argument("--force", action='store_true', help="Get the current IP and force an update")
    parser.add_argument("--interval", type=int, required=False, default=300, help="Frequncy in seconds to poll for updates")
    args = parser.parse_args()
    return args

def get_aws_record(client, domain, zoneid):

    response = client.list_resource_record_sets(HostedZoneId=args.zoneid,
                                                StartRecordName=args.domain,
                                                StartRecordType='A'
                                                )

    record = [record for record in response['ResourceRecordSets'] if record['Name'].rstrip('.') == args.domain]
    
    if len(record) == 0:
        return False, None

    return True, record[0]['ResourceRecords'][0]['Value']

def update_route53(client, domain, zoneid, ttl, ip):

    response = client.change_resource_record_sets(
                HostedZoneId=args.zoneid,
                ChangeBatch={
                    'Comment': 'string',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': domain,
                                'Type': 'A',
                                'TTL': ttl,
                                'ResourceRecords': [
                                    {
                                        'Value': ip
                                    },
                                ],
                            }
                        },
                    ]
                }
            )

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True

    return False

def run(args):

    ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

    # Logging configuration
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # Create AWS boto client
    try:
        client = boto3.client('route53',
                              aws_access_key_id=ACCESS_KEY_ID,
                              aws_secret_access_key=SECRET_ACCESS_KEY
                              )
    except:
        logging.error('Unable to connect to AWS')
        # TODO how to exit clean

    # Get current record in AWS
    success, amazon_ip = get_aws_record(client, args.domain, args.zoneid)

    if success:
        logging.info('Found AWS Route53 record with for {} with IP {}'.format(args.domain, amazon_ip))
    else:
        logging.error('Domain {} not found in Route53.  Exiting'.format(args.domain))
        #sys.exit(1)

    # Get current public ip
    success, current_ip = get_public_ip()

    if success:
        logging.info('Current IP is: {} according to ipify'.format(current_ip))
    else:
        logging.info('Error getting system\'s current IP from ipify')
        return

    # Compare AWS to IPify
    if amazon_ip == current_ip:
        logging.info('Current IP matches Route53 record.  No change needed, exiting'.format(amazon_ip))
        return #sys.exit(0)

    # Update AWS Route53
    logging.warning('Attempting to update Route53 record for {} to resolve to {} with TTL {}'.format(args.domain, current_ip, args.ttl))

    success = update_route53(client, args.domain, args.zoneid, args.ttl, current_ip)

    if success:
        logging.info('Updated Route53 record for {} to {}'.format(args.domain, current_ip))
    else:
        logging.error('Unable to update Route53 DNS entry')

if __name__ == '__main__':

    # Parse arguments
    args = parse_args()

    while 1:
        run(args)
        sleep(args.interval)
