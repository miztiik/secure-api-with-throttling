# -*- coding: utf-8 -*-


import json
import logging
import time
import datetime
import random
import os


class GlobalArgs:
    """ Global statics """
    OWNER = "Mystique"
    ENVIRONMENT = "production"
    MODULE_NAME = "greeter_lambda"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    RANDOM_SLEEP_SECS = int(os.getenv("RANDOM_SLEEP_SECS", 2))
    ANDON_CORD_PULLED = os.getenv("ANDON_CORD_PULLED", False)


def set_logging(lv=GlobalArgs.LOG_LEVEL):
    """ Helper to enable logging """
    logging.basicConfig(level=lv)
    logger = logging.getLogger()
    logger.setLevel(lv)
    return logger


def random_sleep(max_seconds=10):
    if bool(random.getrandbits(1)):
        logger.info(f"sleep_start_time:{str(datetime.datetime.now())}")
        time.sleep(random.randint(0, max_seconds))
        logger.info(f"sleep_end_time:{str(datetime.datetime.now())}")


# Initial some defaults in global context to reduce lambda start time, when re-using container
logger = set_logging(logging.INFO)


def lambda_handler(event, context):
    logger.debug(f"recvd_event:{event}")

    random_sleep(GlobalArgs.RANDOM_SLEEP_SECS)
    return {
        "statusCode": 200,
        "body": f'{{"message": "Hello Miztiikal World, It is {str(datetime.datetime.now())} here! How about there?"}}'
    }
