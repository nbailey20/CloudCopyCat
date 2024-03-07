import json
from classes.ApiCall import ApiCall
from classes.ResourceGroup import Resource
from helpers.config import LAMBDA_RUNTIME, LAMBDA_FUNCTION_NAME, LAMBDA_STATE_FOLDER
from helpers.config import EVENTBRIDGE_RULE_NAME


def dest_lambda_function(dest_account):
    ## Create APIs
    create_function = ApiCall(
        method = "create_function",
        method_args = {
            "FunctionName": LAMBDA_FUNCTION_NAME,
            "Runtime": LAMBDA_RUNTIME,
            "Role": "$dest_lambda_role/arn",
            "Handler": f"{LAMBDA_FUNCTION_NAME}.lambda_handler",
            "Code": {
                "S3Bucket": "$dest_bucket/name",
                "S3Key": f"{LAMBDA_STATE_FOLDER}/{LAMBDA_FUNCTION_NAME}"
            },
            "Timeout": 120
        },
        output_keys = {"arn": "FunctionArn"}
    )
    add_permission = ApiCall(
        method = "add_permission",
        method_args = {
            "FunctionName": LAMBDA_FUNCTION_NAME,
            "StatementId": "CloudCopyCat-EventBridgeInvokePermission",
            "Action": "lambda:InvokeFunction",
            "Principal": "events.amazonaws.com",
            "SourceArn": f"arn:aws:events:$region:{dest_account}:rule/{EVENTBRIDGE_RULE_NAME}",
            "SourceAccount": dest_account
        }
    )

    ## Describe API
    describe_function = ApiCall(
        method = "list_functions",
        output_keys = {
            "arn": f"Functions/?/FunctionName~{LAMBDA_FUNCTION_NAME}/FunctionArn"
        }
    )

    ## Delete API
    delete_function = ApiCall(
        method = "delete_function",
        method_args = {"FunctionName": LAMBDA_FUNCTION_NAME}
    )

    function_resource = Resource(
        name = "dest_lambda_function",
        type = "lambda",
        create_apis = (create_function, add_permission),
        describe_apis = (describe_function,),
        delete_apis = (delete_function,)
    )
    return function_resource
