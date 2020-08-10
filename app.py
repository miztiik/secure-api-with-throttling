#!/usr/bin/env python3

from secure_api_with_throttling.stacks.back_end.unthrottled_api_stack import UnthrottledApiStack
from secure_api_with_throttling.stacks.back_end.secure_throttled_api_stack import SecureThrottledApiStack
from load_generator_stacks.stacks.vpc_stack import VpcStack
from load_generator_stacks.stacks.artillery_load_generator_stack import ArtilleryLoadGeneratorStack

from waf_stacks.waf_stack import WafStack

from aws_cdk import core


app = core.App()

# VPC Stack for hosting Secure API & Other resources
vpc_stack = VpcStack(
    app,
    "load-generator-vpc-stack",
    description="VPC to host resources for generating load on API"
)
# artillery to generate load againstStack for hosting Secure API & Other resources"

# API without any throttling
unthrottled_api = UnthrottledApiStack(
    app,
    "unthrottled-api",
    stack_log_level="INFO",
    back_end_api_name="unthrottled_api_01",
    description="API without any throttling"
)

# Secure your API by throttling requests
secure_api_with_throttling = SecureThrottledApiStack(
    app,
    "secure-throttled-api",
    stack_log_level="INFO",
    back_end_api_name="secure_throttled_api_01",
    description="Secure your API by throttling requests"
)

# Deploy WebAcl with WAF Stack
deploy_waf_stack = WafStack(
    app,
    "waf-stack",
    stack_log_level="INFO",
    secure_api_stage_arn=secure_api_with_throttling.secure_api_stage_arn,
    description="Deploy WebAcl with WAF Stack"
)

# Deploy Artillery Load Testing Stack
load_generator_stack = ArtilleryLoadGeneratorStack(
    app,
    "miztiik-artillery-load-generator",
    vpc=vpc_stack.vpc,
    ec2_instance_type="t2.micro",
    stack_log_level="INFO",
    api_url=secure_api_with_throttling.api_url,
    description="Deploy Artillery Load Testing Stack"
)


# Stack Level Tagging
core.Tag.add(app, key="Owner",
             value=app.node.try_get_context('owner'))
core.Tag.add(app, key="OwnerProfile",
             value=app.node.try_get_context('github_profile'))
core.Tag.add(app, key="GithubRepo",
             value=app.node.try_get_context('github_repo_url'))
core.Tag.add(app, key="Udemy",
             value=app.node.try_get_context('udemy_profile'))
core.Tag.add(app, key="SkillShare",
             value=app.node.try_get_context('skill_profile'))
core.Tag.add(app, key="AboutMe",
             value=app.node.try_get_context('about_me'))


app.synth()
