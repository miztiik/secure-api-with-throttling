from aws_cdk import aws_apigateway as _apigw
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as _logs
from aws_cdk import core

import os


class GlobalArgs:
    """
    Helper to define global statics
    """

    OWNER = "MystiqueAutomation"
    ENVIRONMENT = "production"
    REPO_NAME = "secure-api-with-throttling"
    SOURCE_INFO = f"https://github.com/miztiik/{REPO_NAME}"
    VERSION = "2020_08_03"
    MIZTIIK_SUPPORT_EMAIL = ["mystique@example.com", ]


class UnthrottledApiStack(core.Stack):

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        stack_log_level: str,
        back_end_api_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Read Lambda Code):
        try:
            with open("secure_api_with_throttling/stacks/back_end/lambda_src/serverless_greeter.py", mode="r") as f:
                greeter_fn_code = f.read()
        except OSError as e:
            print("Unable to read Lambda Function Code")
            raise e

        greeter_fn = _lambda.Function(
            self,
            "greeterFn",
            function_name=f"greeter_fn_{id}",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="index.lambda_handler",
            code=_lambda.InlineCode(greeter_fn_code),
            timeout=core.Duration.seconds(10),
            # reserved_concurrent_executions=2,
            environment={
                "LOG_LEVEL": f"{stack_log_level}",
                "Environment": "Production",
                "RANDOM_SLEEP_SECS": "10",
                "ANDON_CORD_PULLED": "False"
            },
            description="Creates a simple greeter function"
        )
        greeter_fn_version = greeter_fn.latest_version
        greeter_fn_version_alias = _lambda.Alias(
            self,
            "greeterFnAlias",
            alias_name="MystiqueAutomation",
            version=greeter_fn_version
        )

        # Create Custom Loggroup
        greeter_fn_lg = _logs.LogGroup(
            self,
            "squareFnLoggroup",
            log_group_name=f"/aws/lambda/{greeter_fn.function_name}",
            retention=_logs.RetentionDays.ONE_WEEK,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Add API GW front end for the Lambda
        back_end_api_stage_01_options = _apigw.StageOptions(
            stage_name="miztiik-unthrottled",
            logging_level=_apigw.MethodLoggingLevel.INFO
        )

        # Create API Gateway
        unthrottled_api = _apigw.RestApi(
            self,
            "backEnd01Api",
            rest_api_name=f"{back_end_api_name}",
            deploy_options=back_end_api_stage_01_options,
            endpoint_types=[
                _apigw.EndpointType.EDGE
            ],
            description=f"{GlobalArgs.OWNER}: API Security Automation demonstration using - Unthrottled API"
        )

        back_end_01_api_res = unthrottled_api.root.add_resource(
            "unsecure")
        greeter = back_end_01_api_res.add_resource("greeter")

        greeter_method_get = greeter.add_method(
            http_method="GET",
            request_parameters={
                "method.request.header.InvocationType": True,
                "method.request.path.number": True
            },
            integration=_apigw.LambdaIntegration(
                handler=greeter_fn,
                proxy=True
            )
        )

        # Outputs
        output_1 = core.CfnOutput(
            self,
            "UnthrottledApiUrl",
            value=f"{greeter.url}",
            description="Use an utility like artitllery to generate load against this API."
        )
