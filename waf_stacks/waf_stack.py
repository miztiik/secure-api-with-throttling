from aws_cdk import aws_wafv2 as _wafv2
from aws_cdk import core

from waf_stacks.custom_resources.waf_rate_rule_creator.waf_rate_rule_creator_stack import WafRateRuleCreatorStack


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


class WafStack(core.Stack):

    def __init__(
            self,
            scope: core.Construct,
            id: str,
            stack_log_level: str,
            secure_api_stage_arn: str,
            rps_limit: str,
            ** kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Your Code):
        # Let us create a Rate Based Rule
        web_acl = _wafv2.CfnWebACL(
            self,
            f"apiSentryAcl-{id}",
            default_action=_wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope="REGIONAL",
            visibility_config=_wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name=f"apiSentryAcl_metrics",
                sampled_requests_enabled=True
            ),
            name=f"apiSentryAcl-{id}",
            description=f"{GlobalArgs.OWNER}: Protect API with Web Application Firewall - Rate Based Rules",
            rules=[]
        )

        # Retrieve Cognito App Client Secret and Add to Secrets Manager
        waf_rule_creator = WafRateRuleCreatorStack(
            self,
            "wafRuleCreator",
            web_acl_name=web_acl.name,
            web_acl_id=web_acl.attr_id,
            web_acl_scope=web_acl.scope,
            rps_limit=rps_limit
        )

        # Export Value
        self.waf_rule_creator_status = waf_rule_creator.response

        # Associate WebAcl to API Gateway
        add_waf_to_resource = _wafv2.CfnWebACLAssociation(
            self,
            id="addWafToApiGw",
            resource_arn=secure_api_stage_arn,
            web_acl_arn=web_acl.attr_arn
        )

        add_waf_to_resource.node.add_dependency(waf_rule_creator)

        # Outputs
        output_0 = core.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )

        output_1 = core.CfnOutput(
            self,
            "WafArn",
            value=f"{web_acl.attr_arn}",
            description="The Web ACL to secure our Api"
        )
        output_2 = core.CfnOutput(
            self,
            "RateRuleCreatorStatus",
            value=f"{self.waf_rule_creator_status}",
            description="Waf Rate Rule Creator Status"
        )
