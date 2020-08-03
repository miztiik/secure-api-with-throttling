#!/usr/bin/env python3

from aws_cdk import core

from secure_api_with_throttling.secure_api_with_throttling_stack import SecureApiWithThrottlingStack


app = core.App()
SecureApiWithThrottlingStack(app, "secure-api-with-throttling")

app.synth()
