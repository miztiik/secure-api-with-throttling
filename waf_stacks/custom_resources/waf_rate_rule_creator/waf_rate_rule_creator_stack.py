from aws_cdk import aws_cloudformation as cfn
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as _logs
from aws_cdk import core


class WafRateRuleCreatorStack(core.Construct):
    def __init__(self, scope: core.Construct, id: str, ** kwargs) -> None:
        super().__init__(scope, id)

        # Read Lambda Code:)
        try:
            with open("waf_stacks/custom_resources/waf_rate_rule_creator/lambda_src/index.py",
                      encoding="utf-8",
                      mode="r"
                      ) as f:
                waf_rate_rule_creator_fn_code = f.read()
        except OSError:
            print("Unable to read Lambda Function Code")
            raise

        # Create IAM Permission Statements that are required by the Lambda

        role_stmt1 = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            resources=["*"],
            actions=[
                "wafv2:GetWebACL",
                "wafv2:UpdateWebACL"
            ]
        )
        role_stmt1.sid = "AllowLambdaToCreateWafRules"

        waf_rate_rule_creator_fn = _lambda.SingletonFunction(
            self,
            "waFRateRuleCreatorSingleton",
            uuid="mystique30-4ee1-11e8-9c2d-fa7ae01bbebc",
            code=_lambda.InlineCode(
                waf_rate_rule_creator_fn_code),
            handler="index.lambda_handler",
            timeout=core.Duration.seconds(10),
            runtime=_lambda.Runtime.PYTHON_3_7,
            reserved_concurrent_executions=1,
            environment={
                "LOG_LEVEL": "INFO",
                "APP_ENV": "Production"
            },
            description="Creates a rate based WAF rule"
        )

        waf_rate_rule_creator_fn.add_to_role_policy(role_stmt1)

        # Create Custom Log group
        waf_rate_rule_creator_fn_lg = _logs.LogGroup(
            self,
            "wafRateRuleCreatorLogGroup",
            log_group_name=f"/aws/lambda/{waf_rate_rule_creator_fn.function_name}",
            retention=_logs.RetentionDays.ONE_WEEK,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        waf_rate_rule_creator = cfn.CustomResource(
            self,
            "wafRateRuleCreatorCustomResource",
            provider=cfn.CustomResourceProvider.lambda_(
                waf_rate_rule_creator_fn
            ),
            properties=kwargs,
        )

        self.response = waf_rate_rule_creator.get_att(
            "rule_add_status").to_string()
