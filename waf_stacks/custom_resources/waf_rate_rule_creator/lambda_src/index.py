# -*- coding: utf-8 -*-

import logging as log
import os
import json
import boto3
import cfnresponse
log.getLogger().setLevel(log.INFO)

_wafv2_client = boto3.client("wafv2")


class GlobalArgs:
    OWNER = "Mystique"
    ENVIRONMENT = "production"


def _get_web_acl(web_acl_name, web_acl_id, web_acl_scope):
    _web_acl_info = ""
    try:
        _web_acl_info = _wafv2_client.get_web_acl(
            Name=web_acl_name,
            Scope=web_acl_scope,
            Id=web_acl_id
        )
        log.info(f"_web_acl_info: {_web_acl_info}")
    except Exception as e:
        log.error(f"GetWebAclInfo: {str(e)}")
    return _web_acl_info


def _update_web_acl(web_acl_name, web_acl_id, web_acl_scope, rps_limit, lock_token):
    _r = ""
    try:
        res = _wafv2_client.update_web_acl(
            Name=web_acl_name,
            Scope=web_acl_scope,
            Id=web_acl_id,
            DefaultAction={"Allow": {}},
            Description=f"{GlobalArgs.OWNER}: Protect API with Web Application Firewall - Rate Based Rules",
            Rules=[
                {
                    "Name": f'limit_rps_to_{rps_limit}',
                    'Priority': 133,
                    'Action': {
                        'Block': {}
                    },
                    'Statement': {
                        'RateBasedStatement': {
                            'Limit': rps_limit,
                            'AggregateKeyType': 'IP',
                        }
                    },
                    'VisibilityConfig': {
                        'SampledRequestsEnabled': True,
                        'CloudWatchMetricsEnabled': True,
                        'MetricName': f'limit_rps_to_{rps_limit}_metric'
                    }

                }
            ],
            VisibilityConfig={
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'secureApiThrottlingMetric'
            },
            LockToken=lock_token
        )
        log.info(f"rule_update_res: {res}")
        _r = res.get("ResponseMetadata").get("HTTPStatusCode")
    except Exception as e:
        log.error(f"UpdateWebAclError: {str(e)}")
    return _r


def lambda_handler(event, context):
    log.info(f"event: {event}")
    physical_id = 'MystiqueAutomationCustomRes'

    try:
        # MINE
        cfn_stack_name = event.get("StackId").split("/")[-2]
        resource_id = event.get("LogicalResourceId")
        res = ""
        web_acl_name = event["ResourceProperties"].get("Web_acl_name")
        web_acl_id = event["ResourceProperties"].get("Web_acl_id")
        web_acl_scope = event["ResourceProperties"].get("Web_acl_scope")
        rps_limit = int(event["ResourceProperties"].get("Rps_limit", 110))

        # Get the Acl Info
        _web_acl_info = _get_web_acl(web_acl_name, web_acl_id, web_acl_scope)

        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            log.info(f"FailCreate")
            raise RuntimeError("Create failure requested")
        if event["RequestType"] == "Create":
            res = _update_web_acl(
                web_acl_name, web_acl_id, web_acl_scope, rps_limit, _web_acl_info.get("LockToken"))
        elif event["RequestType"] == "Update":
            res = "no_updates_made"
            pass
        elif event["RequestType"] == "Delete":
            res = "delete_triggered"
            pass
        else:
            log.error("FAILED!")
            return cfnresponse.send(event, context, cfnresponse.FAILED, attributes, physical_id)

        # MINE
        attributes = {
            "rule_add_status": f"HTTPStatusCode-{res}"
        }
        cfnresponse.send(event, context, cfnresponse.SUCCESS,
                         attributes, physical_id)
    except Exception as e:
        log.exception(e)
        cfnresponse.send(event, context, cfnresponse.FAILED,
                         attributes, physical_id)
