from classes.ApiCall import ApiCall
from classes.ResourceGroup import ResourceGroup
from helpers.config import LAMBDA_STATE_FOLDER, LAMBDA_STATE_FILE_NAME
from helpers.config import BATCH_COPY_ROLE_NAME


def get_param_data(src_account, dest_account):
    return [
        {
            "name": "CloudCopyCat-Source-Account-ID",
            "value": src_account,
            "type": "ssm"
        },
        {
            "name": "CloudCopyCat-State-File-Path",
            "value": f"{LAMBDA_STATE_FOLDER}/{LAMBDA_STATE_FILE_NAME}",
            "type": "ssm"
        },
        {
            "Name": "CloudCopyCat-Batch-Copy-Role-Arn",
            "Value": f"arn:aws:iam::{dest_account}:role/{BATCH_COPY_ROLE_NAME}",
            "type": "ssm"
        }
    ]


def dest_ssm_param(src_account, dest_account):
    ## Create API
    create_param = ApiCall(
        method = "put_parameter",
        method_args = {
            "Name": "$dest_ssm_param/#id/name",
            "Value": "$dest_ssm_param/#id/value",
            "Type": "SecureString",
            "KeyId": "$dest_kms_key/arn"
        }
    )

    ## Describe API
    describe_param  = ApiCall(
        method = "describe_parameters",
        method_args = {
            "ParameterFilters": [{
                "Key": "Name",
                "Values": [
                    "$dest_ssm_param/#id/name"
                ]
            }]
        },
        output_keys = {"arn": "Parameters/*/Arn"}
    )

    ## Delete API
    delete_param = ApiCall(
        method = "delete_parameter",
        method_args = {"Name": "$dest_ssm_param/#id/name"}
    )

    state = {
        "dest_ssm_param": [
            {
                "name": "CloudCopyCat-Source-Account-ID",
                "value": src_account
            },
            {
                "name": "CloudCopyCat-State-File-Path",
                "value": f"{LAMBDA_STATE_FOLDER}/{LAMBDA_STATE_FILE_NAME}"
            },
            {
                "Name": "CloudCopyCat-Batch-Copy-Role-Arn",
                "Value": f"arn:aws:iam::{dest_account}:role/{BATCH_COPY_ROLE_NAME}"
            }
        ]
    }
    param_resource = ResourceGroup(
        name = "dest_ssm_param",
        type = "ssm",
        create_apis = (create_param,),
        describe_apis = (describe_param,),
        delete_apis = (delete_param,),
        state = state
    )
    return param_resource
