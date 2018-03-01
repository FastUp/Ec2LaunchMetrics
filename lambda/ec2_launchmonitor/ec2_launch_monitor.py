from __future__ import print_function

import datetime
import json
import sys
import traceback

import boto3

cw_client = boto3.client('cloudwatch')
ec2_client = boto3.client('ec2')




def run(event, context):
    try:
        config = json.load(open("ec2_launch_monitor.config.json"))
        print(json.dumps(event))
        instance_state = event["detail"]["state"]
        instance = ec2_client.describe_instances(InstanceIds=[event["detail"]["instance-id"]])
        instance_type = instance["Reservations"][0]["Instances"][0]["InstanceType"]
        now = datetime.datetime.now()
        if instance_state in ["pending", "terminated", "stopped"]:
            if instance_state == "pending":
                state_dim = "started"
            else:
                state_dim = "stopped"
            dimensions = [{'Name': 'State', 'Value': state_dim}, {'Name': 'InstanceType', 'Value': instance_type}]
            put_metric(config, dimensions, now)
            dimensions = [{'Name': 'State', 'Value': state_dim}]
            put_metric(config, dimensions, now)
            if instance_type.startswith("t"):
                dimensions = [
                    {'Name': 'BurstableTTypeState', 'Value': state_dim}
                ]
                put_metric(config, dimensions, now)

    except BaseException as be:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        raise be


def put_metric(config, dimensions, when):
    response = cw_client.put_metric_data(
        Namespace=config["MetricNameSpace"],
        MetricData=[
            {
                'MetricName': config["MetricName"],
                'Dimensions': dimensions,
                'Timestamp': when,
                'Value': 1,

                'Unit': 'Count'
            },
        ]
    )
    return response


if __name__ == "__main__":
    ### Test event for local. Replace account numbers, ids as needed###
    run({
        "account": "111111111111",
        "region": "us-east-1",
        "detail": {
            "state": "pending",
            "instance-id": "i-xxxxxxxxxxxxxxxxxx"
        },
        "detail-type": "EC2 Instance State-change Notification",
        "source": "aws.ec2",
        "version": "0",
        "time": "2017-04-21T14:17:06Z",
        "id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "resources": [
            "arn:aws:ec2:us-east-1:111111111111:instance/i-xxxxxxxxxxxxxxxxx"
        ]
    }, None)
