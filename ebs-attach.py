#!/usr/bin/python2

import argparse
import os
import signal
import sys
import time

import boto.ec2
import boto.exception
import requests

# on close, detach ebs
parser = argparse.ArgumentParser(
    description='Attach and mount EBS volume to local instance')
parser.add_argument('--volumeid', metavar='<VOLUME_ID>', default=None,
                    help='Volume ID of EBS volume to attach')
parser.add_argument('--device', metavar='<DEVICE>', default=None,
                    help='Device to expose volume on')
parser.add_argument('--region', metavar='<REGION>', default=None,
                    help='AWS region in which the EBS resides')
parser.add_argument('--access-key', metavar='<ACCESS>', default=None)
parser.add_argument('--secret-key', metavar='<SECRET>', default=None)
args = parser.parse_args()

# AWS metadata service that provides credentials is unreliable
# so retry several times
attempts = 0
while True:
    try:
        conn = boto.ec2.connect_to_region(args.region,
                                          aws_access_key_id=args.access_key,
                                          aws_secret_access_key=args.secret_key)
    except boto.exception.NoAuthHandlerFound:
        print "Couldn't find auth credentials handler, trying again"
        sys.stdout.flush()

        attempts += 1
        if attempts > 5:
            print "Tried 5 times, giving up"
            sys.exit(3)
        else:
            time.sleep(1)
    else:
        break

instance = requests.get("http://169.254.169.254/latest/meta-data/instance-id").content

existing_vols = conn.get_all_volumes([args.volumeid])
if len(existing_vols) > 0:
    vol = existing_vols[0]

    if vol.attach_data.instance_id == instance:
        print "Volume {} already attached to {}".format(args.volumeid, instance)
        sys.stdout.flush()
    else:
        conn.attach_volume(args.volumeid, instance, args.device) or sys.exit(1)
        print "Attached volume {} to device {} on instance {}".format(args.volumeid, args.device, instance)
        sys.stdout.flush()
else:
    print "Cannot find volume {}".format(args.volumeid)
    sys.exit(2)


def detach_func(volume, instance, device):
    def handler(*args, **kwargs):
        attempts = 0

        while True:
            try:
                print "Detaching volume {} from device {} on instance {}".format(volume, device, instance)
                conn.detach_volume(volume, instance, device)
            except boto.exception.NoAuthHandlerFound:
                print "Couldn't find auth credentials handler, trying again"
                sys.stdout.flush()

                attempts += 1
                if attempts > 5:
                    print "Tried 5 times, giving up"
                    sys.exit(3)
                else:
                    time.sleep(1)
            else:
                sys.exit(0)
    return handler

detach = detach_func(args.volumeid, instance, args.device)
signal.signal(signal.SIGTERM, detach)
signal.signal(signal.SIGINT, detach)

while True:
    time.sleep(5)
