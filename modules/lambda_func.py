from helpers.config import LAMBDA_RUNTIME, LAMBDA_FUNCTION_NAME

from modules.s3 import create_s3_object
from modules.sts import get_account_id


def create_lambda(session, role_arn, bucket_name, kms_arn):
    create_s3_object(session, 
                     bucket_name, 
                     f"CloudCopyCat-Data/{LAMBDA_FUNCTION_NAME}", 
                     filename=f"resources/lambda/{LAMBDA_FUNCTION_NAME}.zip"
                    )

    client = session.client("lambda")
    lambda_function_arn = client.create_function(
        FunctionName = LAMBDA_FUNCTION_NAME,
        Runtime      = LAMBDA_RUNTIME,
        Role         = role_arn,
        Handler      = f"{LAMBDA_FUNCTION_NAME}.lambda_handler",
        Code = {
            "S3Bucket": bucket_name,
            "S3Key": f"CloudCopyCat-Data/{LAMBDA_FUNCTION_NAME}"
        },
        Timeout   = 120,
        KMSKeyArn = kms_arn
    )["FunctionArn"]

    return lambda_function_arn



def add_lambda_permission(session, rule_arn):
    account_id = get_account_id(session=session)
    client = session.client("lambda")

    client.add_permission(
        FunctionName  = LAMBDA_FUNCTION_NAME,
        StatementId   = "EventBridgeInvokePermission",
        Action        = "lambda:InvokeFunction",
        Principal     = "events.amazonaws.com",
        SourceArn     = rule_arn,
        SourceAccount = account_id
    )
    return




def delete_lambda(session):
    client = session.client("lambda")
    client.delete_function(
        FunctionName = LAMBDA_FUNCTION_NAME
    )
    return