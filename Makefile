.PHONY: test help clean
.DEFAULT_GOAL := help

# Global Variables
CURRENT_PWD:=$(shell pwd)
VENV_DIR:=.env
AWS_PROFILE:=elf

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


install: ## Install CDK and bootstrap
	npm -g install aws-cdk
	cdk bootstrap

init: ## Initialize a empty project using python language
	cdk init app --language python

cdk_ls: ## List the stacks
	/bin/bash -c "cd $(CURRENT_PWD) && . .env/bin/activate && cdk ls"


pre_build: ## Run build
	npm run build


build: ## Synthesize the template
	cdk synth

post_build: ## Show differences
	cdk diff

deploy: ## Deploy ALL stack
	cdk deploy load-generator-vpc-stack --profile ${AWS_PROFILE} --require-approval never
	cdk deploy secure-throttled-api --profile ${AWS_PROFILE} --require-approval never
	cdk deploy unthrottled-api --profile ${AWS_PROFILE} --require-approval never
	cdk deploy miztiik-artillery-load-generator --profile ${AWS_PROFILE} --require-approval never
	cdk deploy waf-stack --profile ${AWS_PROFILE} --require-approval never

destroy: ## Delete Stack without confirmation
	cdk destroy load-generator-vpc-stack --profile ${AWS_PROFILE} --require-approval never
	cdk destroy secure-throttled-api --profile ${AWS_PROFILE} --require-approval never
	cdk destroy unthrottled-api --profile ${AWS_PROFILE} --require-approval never
	cdk destroy miztiik-artillery-load-generator --profile ${AWS_PROFILE} --require-approval never
	cdk destroy waf-stack --profile ${AWS_PROFILE} --require-approval never

deps: deps_python ## Install dependancies

deps_python:
	.env/bin/activate
	pip3 install -r requirements.txt


clean: ## Remove All virtualenvs
	@rm -rf ${PWD}/${VENV_DIR} build dist *.egg-info .eggs .pytest_cache .coverage
	@find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf
