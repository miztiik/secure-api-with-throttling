# Security best practices in Amazon API Gateway

Mystique Unicorn App is a containerized microservice made of many APIs. As Mystique Corp is dealing with Personally Identifiable Information(PII) data, they intend to secure their api. Ideally the APIs should be accessible from within their own corporate networks only and all other access to the APIs should be denied.

![Miztiik Asynchronous Messaging with AWS Lambda](images/miztiik_messaging.png)

We recommend that you add web ACLs and rate-based rules as part of your AWS Shield Advanced protections. These rules can alert you to sudden spikes in traffic that might indicate a potential DDoS event. A rate-based rule counts the requests that arrive from any individual address in any five minute period. If the number of requests exceeds the limit defined by you, the rule can trigger an action such as sending you a notification.

To prevent your API from being overwhelmed by too many requests, You can throttles requests to your API. You can set the limits for individual API stages or methods to improve overall performance across all APIs in your account. Set a limit on a steady-state rate and a burst of request submissions. When request submissions exceed the steady-state request rate and burst limits, API Gateway fails the limit-exceeding requests and returns `429 Too Many Requests` error responses to the client.

_Note:_ By default, API Gateway limits the steady-state request rate to `10000` requests per second (rps). It limits the burst (that is, the maximum bucket size) to `5000` requests across all APIs within an AWS account.

![Miztiik Serverless API Authorization](images/miztiik_secure_private_api.png)

In this article, we will build the above architecture. using Cloudformation generated using [AWS Cloud Development Kit (CDK)][102]. The architecture has been designed in a modular way so that we can build them individually and integrate them together. The prerequisites to build this architecture are listed below

1. ## 🧰 Prerequisites

   This demo, instructions, scripts and cloudformation template is designed to be run in `us-east-1`. With few modifications you can try it out in other regions as well(_Not covered here_).

   - 🛠 AWS CLI Installed & Configured - [Get help here](https://youtu.be/TPyyfmQte0U)
   - 🛠 AWS CDK Installed & Configured - [Get help here](https://www.youtube.com/watch?v=MKwxpszw0Rc)
   - 🛠 Python Packages, _Change the below commands to suit your OS, the following is written for amzn linux 2_
     - Python3 - `yum install -y python3`
     - Python Pip - `yum install -y python-pip`
     - Virtualenv - `pip3 install virtualenv`

1. ## ⚙️ Setting up the environment

   - Get the application code

     ```bash
     git clone https://github.com/miztiik/secure-private-api.git
     cd secure-private-api
     ```

1. ## 🚀 Prepare the dev environment to run AWS CDK

   We will cdk to be installed to make our deployments easier. Lets go ahead and install the necessary components.

   ```bash
   # If you DONT have cdk installed
   npm install -g aws-cdk

   # Make sure you in root directory
   python3 -m venv .env
   source .env/bin/activate
   pip3 install -r requirements.txt
   ```

   The very first time you deploy an AWS CDK app into an environment _(account/region)_, you’ll need to install a `bootstrap stack`, Otherwise just go ahead and deploy using `cdk deploy`.

   ```bash
   cdk bootstrap
   cdk ls
   # Follow on screen prompts
   ```

   You should see an output of the available stacks,

   ```bash
   unsecure-public-api
   secure-private-api-vpc-stack
   secure-private-api
   api-consumer
   ```

1. ## 🚀 Deploying the application

   Let us walk through each of the stacks,

   - **Stack: unsecure-public-api**
     We are going to deploy a simple `greeter` api. This API is deployed as public endpoing to illustrate that any one in the internet can access the API and it is unsecure. When the api is invoked, It returns a welcome message along with the lambda ip address. We should be able to invoke the function from a browser or using an utility like `curl`.

     Initiate the deployment with the following command,

     ```bash
     cdk deploy unsecure-public-api
     ```

     _Expected output:_
     The `ApiUrl` can be found in the outputs section of the stack,

     ```json
     {
       "message": "Hi Miztikal World, Hello from Lambda running at 3.237.174.199"
     }
     ```

   - **Stack: secure-private-api**

     Now that we have understand that public APIs are accessible by everyone. Let us see how to build an secure API. To secure the API, we are going to deploy as `PRIVATE` type API and make it accessible only from a custom VPC. To add another layer of security, we can have a custom defined security group attached to the API.

     This stack:_secure-private-api_ is dependant on the `secure-private-api-vpc-stack`. If you are using CDK, it will be deployed for you. If not go ahead and deploy that as well. The following resources are created by these two stacks,

     - A Custom VPC ( without NAT Instances )
       - API Gateway VPCE Endpoint
       - Custom Security Group allowing port `443` from within the VPC
     - Deploy an API Gateway with an lambda function backend
       - Attach a API Gateway Resource Policy, to make the API accessible only from the VPC


        Initiate the deployment with the following command,

        ```bash
        cdk deploy secure-private-api-vpc-stack
        cdk deploy secure-private-api
        ```

        Check the `Outputs` section of the stack to access the `SecureApiUrl`

1.  ## 🔬 Testing the solution

    The _Outputs_ section of the `secure-private-api` stack has the required information on the urls

    - We need to invoke the `SecureApiUrl` from the same VPC. To make it easier to test the solution, I have created another template that will deploy an EC2 instance in the same VPC and in the same security group as the API Gateway. You can login to the instances using [Systems Manager](https://www.youtube.com/watch?v=-ASMtZBrx-k). You can deploy this stack or create your own instance.

      Initiate the deployment with the following command,

      ```bash
      cdk deploy api-consumer
      ```

      ```bash
      API_URL="https://pp3dmyx3gh.execute-api.us-east-1.amazonaws.com/miztiik/secure/greeter"
      artillery quick -n 2000 --count 10  ${API_URL}
      artillery quick -d 600 -n 2000 --count 10  ${API_URL}
      ```

      Expected Output,

      ```bash
      sh-4.2$ curl -X GET https://p35nrnhb3m.execute-api.us-east-1.amazonaws.com/miztiik/secure/greeter
      {"message": "Hi Miztiikal World, Hello from Lambda running at 3.235.133.156"}
      ```

      Get the list of IP addresses blocked by rate-based rules

      ```bash
      aws wafv2 get-rate-based-statement-managed-keys --scope=REGIONAL --region=us-east-1 --web-acl-name=apiSentryAclwaf-stack --web-acl-id=b4d665ec-151a-44cd-a8ec-b147136faa52 --rule-name=rps_110
      ```

      ```bash
      ]$ aws wafv2 get-rate-based-statement-managed-keys \
          --scope REGIONAL \
          --region us-east-1 \
          --web-acl-name apiSentryAclwaf-stack \
          --web-acl-id b4d665ec-151a-44cd-a8ec-b147136faa52 \
          --rule-name rps_110

        {
            "ManagedKeysIPV4": {
                "IPAddressVersion": "IPV4",
                "Addresses": [
                    "3.236.176.254/32"
                ]
            },
            "ManagedKeysIPV6": {
                "IPAddressVersion": "IPV6",
                "Addresses": []
            }
        }
      ```

You should be able to see the public IP address of EC2 instances being blocked by WAF. This IP will be automatically unblocked by WAF if the requests fall below the threshold in any `5-Minute` period.

    _Additional Learnings:_ You can check the logs in cloudwatch for more information or increase the logging level of the lambda functions by changing the environment variable from `INFO` to `DEBUG`

1.  ## 🧹 CleanUp

    If you want to destroy all the resources created by the stack, Execute the below command to delete the stack, or _you can delete the stack from console as well_

    - Resources created during [deployment](#-resource-deployment-using-aws-cdk)
    - Delete CloudWatch Lambda LogGroups
    - _Any other custom resources, you have created for this demo_

    ```bash
    # Delete from cdk
    cdk destroy cognito-identity-provider

    # Follow any on-screen prompts

    # Delete the CF Stack, If you used cloudformation to deploy the stack.
    aws cloudformation delete-stack \
        --stack-name "MiztiikAutomationStack" \
        --region "${AWS_REGION}"
    ```

    This is not an exhaustive list, please carry out other necessary steps as maybe applicable to your needs.

## 📌 Who is using this

This repository to teaches cloudformation to new developers, Solution Architects & Ops Engineers in AWS. Based on that knowledge these Udemy [course #1][103], [course #2][102] helps you build complete architecture in AWS.

### 💡 Help/Suggestions or 🐛 Bugs

Thank you for your interest in contributing to our project. Whether it's a bug report, new feature, correction, or additional documentation or solutions, we greatly value feedback and contributions from our community. [Start here][200]

### 👋 Buy me a coffee

[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Q5Q41QDGK)Buy me a [coffee ☕][900].

### 📚 References

1. [Throttle API requests for better throughput][1]

1. [Troubleshoot API Gateway private API endpoint issues][2]

1. [Security best practices in Amazon API Gateway][3]

1. [Controlling and managing access to a REST API in API Gateway][4]

1. [Protecting APIs using AWS WAF][5]

1. [Access private REST API in another account using an interface VPC endpoint][6]

1. [IAM policy examples for API execution permissions][7]

1. [VPC endpoint policies for private APIs in API Gateway][8]

1. [DNS with AWS Client VPN endpoint][10]

### 🏷️ Metadata

**Level**: 300

![miztiik-success-green](https://img.shields.io/badge/miztiik-success-green)

https://docs.aws.amazon.com/waf/latest/APIReference/API_UpdateWebACL.html
https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-troubleshoot-403-forbidden/

[1]: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html
[2]: https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-private-endpoint-connection/
[3]: https://docs.aws.amazon.com/apigateway/latest/developerguide/security-best-practices.html
[4]: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html
[5]: https://aws.amazon.com/blogs/compute/protecting-your-api-using-amazon-api-gateway-and-aws-waf-part-i/
[6]: https://www.youtube.com/watch?v=UnoVqaTGwzM
[7]: https://aws.amazon.com/blogs/compute/protecting-your-api-using-amazon-api-gateway-and-aws-waf-part-2/
[8]: https://aws.amazon.com/blogs/compute/building-well-architected-serverless-applications-controlling-serverless-api-access-part-2/
[100]: https://www.udemy.com/course/aws-cloud-security/?referralCode=B7F1B6C78B45ADAF77A9
[101]: https://www.udemy.com/course/aws-cloud-security-proactive-way/?referralCode=71DC542AD4481309A441
[102]: https://www.udemy.com/course/aws-cloud-development-kit-from-beginner-to-professional/?referralCode=E15D7FB64E417C547579
[103]: https://www.udemy.com/course/aws-cloudformation-basics?referralCode=93AD3B1530BC871093D6
[200]: https://github.com/miztiik/secure-private-api/issues
[899]: https://www.udemy.com/user/n-kumar/
[900]: https://ko-fi.com/miztiik
[901]: https://ko-fi.com/Q5Q41QDGK
