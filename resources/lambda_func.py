import time
from classes.ApiCall import ApiCall
from classes.ResourceGroup import Resource
from classes.Transformer import Transformer
from helpers.config import LAMBDA_RUNTIME, LAMBDA_FUNCTION_NAME, LAMBDA_STATE_FOLDER
from helpers.config import EVENTBRIDGE_RULE_NAME


def dest_lambda_function(dest_account, suffix):
    lambda_name = f"{LAMBDA_FUNCTION_NAME}-{suffix}"
    eb_name = f"{EVENTBRIDGE_RULE_NAME}-{suffix}"

    ## Create APIs
    def sleep_for_15():
        print("Sleeping for 15 to let Lambda role fully create")
        time.sleep(15)
    wait_for_lambda_role = Transformer(
        func = sleep_for_15
    )
    create_function = ApiCall(
        method = "create_function",
        method_args = {
            "FunctionName": lambda_name,
            "Runtime": LAMBDA_RUNTIME,
            "Role": "$dest_lambda_role/arn",
            "Handler": f"{lambda_name}.lambda_handler",
            "Code": {
                "S3Bucket": "$dest_bucket/name",
                "S3Key": f"{LAMBDA_STATE_FOLDER}/{lambda_name}"
            },
            "Timeout": 120
        },
        output_keys = {"arn": "FunctionArn"}
    )
    add_permission = ApiCall(
        method = "add_permission",
        method_args = {
            "FunctionName": lambda_name,
            "StatementId": "CloudCopyCat-EventBridgeInvokePermission",
            "Action": "lambda:InvokeFunction",
            "Principal": "events.amazonaws.com",
            "SourceArn": f"arn:aws:events:$region:{dest_account}:rule/{eb_name}",
            "SourceAccount": dest_account
        }
    )

    ## Describe API
    describe_function = ApiCall(
        method = "list_functions",
        output_keys = {
            "arn": f"Functions/?/FunctionName~{lambda_name}/FunctionArn"
        }
    )

    ## Delete API
    delete_function = ApiCall(
        method = "delete_function",
        method_args = {"FunctionName": lambda_name}
    )

    function_resource = Resource(
        name = "dest_lambda_function",
        type = "lambda",
        create_apis = (wait_for_lambda_role, create_function, add_permission),
        describe_apis = (describe_function,),
        delete_apis = (delete_function,)
    )
    return function_resource
