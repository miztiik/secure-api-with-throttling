#!/usr/bin/env python3
# version: 05Apr2020
import json
import logging
import os
import random
import string
import time
import uuid

import boto3

import constants


logging.basicConfig(filename=f"{constants.LOG_FILE_NAME}",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=os.getenv('LOG_LEVEL', 'INFO').upper()
                    )
LOGGER = logging.getLogger()

##################################################
#############     SET GLOBALS     ################
##################################################

NO_OF_RECORDS = int(constants.NO_OF_RECORDS)
FREQUENCY = int(constants.FREQUENCY)
DURATION = int(constants.DURATION)
DELAY = int(constants.DELAY)
AWS_REGION = str(constants.AWS_REGION)
# STREAM_NAME = os.getenv("STREAM_NAME", "data_pipe")
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


class global_args:
    """
    Helper to define global statics
    """
    OWNER = "MystiqueAutomation"
    REPO_NAME = "stream-data-processor"
    SOURCE_INFO = f"https://github.com/miztiik/{REPO_NAME}"
    VERSION = "2020_04_05"


input_file = "./../../data/covid19_india_04_apr_2020.json"

client = boto3.client(
    'kinesis', region_name=AWS_REGION)
ssm_client = boto3.client('ssm', region_name=AWS_REGION)


res = ssm_client.get_parameter(
    Name=f"/{global_args.REPO_NAME}/streams/data_pipe/stream_name",
    WithDecryption=True
)

STREAM_NAME = res['Parameter']['Value']


def _gen_uuid():
    """ Generates a uuid string and return it """
    return str(uuid.uuid4())


def random_str_generator(size=40, chars=string.ascii_uppercase + string.digits):
    ''' Generate Random String for given string length '''
    return ''.join(random.choice(chars) for _ in range(size))


with open(input_file, mode="r", encoding="utf-8-sig") as f:
    p_data = json.load(f)
    p_len = len(p_data)


def send_data(client, data, key, stream_name):
    # LOGGER.info(f"data:{json.dumps(data)}")
    # LOGGER.info(f"key:{key}")
    resp = client.put_records(
        Records=[
            {
                'Data': json.dumps(data),
                'PartitionKey': key},
        ],
        StreamName=stream_name

    )
    # LOGGER.info(f"Response:{resp}")


"""
Loop for approximate length of the json
# Can use len(p_data)
"""


def manual_send_records():
    for i in range(random.randint(2, 3)):
        time.sleep(5)
        records = []

        send_data(client, {"name": random_str_generator(8)},
                  _gen_uuid(), STREAM_NAME)
        # send_data(client, {"name": random_str_generator(8)}, _gen_uuid(), STREAM_NAME)
        # send_data(client, {"name": random_str_generator(i)}, _gen_uuid(), STREAM_NAME)


def auto_send_records():
    tot_records = 0
    LOGGER.info(f"Begin sending records for '{DURATION}' seconds")
    # Get epoch time in seconds
    start_time = int(time.time())
    while True:
        for i in range(NO_OF_RECORDS):
            d = {}
            r = random.randint(1, p_len)
            d["patient_number"] = p_data[r]["patient_number"]
            d["date_announced"] = p_data[r]["date_announced"]
            d["state_code"] = p_data[r]["state_code"]
            d["age_bracket"] = p_data[r]["age_bracket"]
            d["gender"] = p_data[r]["gender"]
            send_data(client, d, _gen_uuid(), STREAM_NAME)
            # Delay between records
            time.sleep(DELAY)
            # LOGGER.info("Sleeping for 1 second between records")
            tot_records += 1
        # Frequency, between 'batch of records'
        time.sleep(FREQUENCY)
        LOGGER.info(
            f"Pause sending records to match frequency, Sending every {FREQUENCY} seconds")
        curr_time = int(time.time())
        elapsed_time = curr_time - start_time
        print(f'{{"records_in_progress":{tot_records},"elapsed_time":{elapsed_time}}}')
        # LOGGER.info(f'{{"records_produced":{tot_records},"elapsed_time":{elapsed_time}}}')
        LOGGER.info(f"Remaining Time:{DURATION - elapsed_time}")
        if elapsed_time >= DURATION:
            LOGGER.info(
                f'{{"records_produced":{tot_records},"elapsed_time":{elapsed_time}}}')
            print(
                f'{{"records_produced":{tot_records},"elapsed_time":{elapsed_time}}}')
            break


auto_send_records()
