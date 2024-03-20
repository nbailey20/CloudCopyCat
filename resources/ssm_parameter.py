from classes.ApiCall import ApiCall
from classes.Transformer import Transformer
from classes.ResourceGroup import ResourceGroup
from helpers.config import LAMBDA_STATE_FOLDER, LAMBDA_STATE_FILE_NAME
from helpers.config import BATCH_COPY_ROLE_NAME


def get_param_data(src_account, dest_account, suffix):
    batch_name = f"{BATCH_COPY_ROLE_NAME}-{suffix}"
    return [
        {
            "name": f"CloudCopyCat-Source-Account-ID-{suffix}",
            "value": src_account,
            "type": "ssm"
        },
        {
            "name": f"CloudCopyCat-State-File-Path-{suffix}",
            "value": f"{LAMBDA_STATE_FOLDER}/{LAMBDA_STATE_FILE_NAME}",
            "type": "ssm"
        },
        {
            "name": f"CloudCopyCat-Batch-Copy-Role-Arn-{suffix}",
            "value": f"arn:aws:iam::{dest_account}:role/{batch_name}",
            "type": "ssm"
        }
    ]


def dest_ssm_param():
    def build_arn_from_name(name=None, region=None, account=None):
        if name == "null":
            return {"arn": None}
        return {"arn": f"arn:aws:ssm:{region}:{account}:parameter/{name}"}
    generate_arn = Transformer(
        func = build_arn_from_name,
        function_args = {
            "name": "$dest_ssm_param/#id/arn",
            "region": "$region",
            "account": "$dest_account"
        },
        output_keys = ["arn"]
    )

    ## Create API
    create_param = ApiCall(
        method = "put_parameter",
        method_args = {
            "Name": "$dest_ssm_param/#id/name",
            "Value": "$dest_ssm_param/#id/value",
            "Type": "SecureString",
            "KeyId": "$dest_kms_key/arn"
        },
        output_keys = {"arn": "$dest_ssm_param/#id/name"}
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
        output_keys = {"arn": "Parameters/?/Name~${dest_ssm_param/#id/name}/Name"}
    )

    ## Delete API
    delete_param = ApiCall(
        method = "delete_parameter",
        method_args = {"Name": "$dest_ssm_param/#id/name"}
    )

    param_resource = ResourceGroup(
        name = "dest_ssm_param",
        type = "ssm",
        create_apis = (create_param, generate_arn),
        describe_apis = (describe_param, generate_arn),
        delete_apis = (delete_param,)
    )
    return param_resource
