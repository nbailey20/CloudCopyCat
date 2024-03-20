import time
from classes.ApiCall import ApiCall
from classes.Transformer import Transformer
from classes.ResourceGroup import ResourceGroup


def src_batch_replication(suffix, force=False):
    job_description = "CloudCopyCat-${src_bucket/#id/name}-Replication-Job-" + suffix

    ## Creation API
    def sleep_for_20():
        print("Sleeping for 20 to let Lambda function / EventBridge rule fully create")
        time.sleep(20)
    wait_for_lambda_and_rule = Transformer(
        func = sleep_for_20
    )
    create_job = ApiCall(
        method = "create_job",
        method_args = {
            "AccountId": "$src_account",
            "ConfirmationRequired": True,
            "Operation": {
                "S3ReplicateObject": {}
            },
            "Report": {
                "Enabled": False
            },
            "Description": job_description,
            "Priority": 10,
            "RoleArn": "$src_replication_role/arn",
            "ManifestGenerator": {
                "S3JobManifestGenerator": {
                    "SourceBucket": "$src_bucket/#id/arn",
                    "ManifestOutputLocation": {
                        "Bucket": "$dest_bucket/arn",
                        "ManifestPrefix":              "CloudCopyCat-Data/${src_bucket/#id/name}/InvReport",
                        "ManifestFormat":              "S3InventoryReport_CSV_20211130",
                        "ExpectedManifestBucketOwner": "$dest_account",
                        "ManifestEncryption": {
                            "SSEKMS": {
                                "KeyId": "$dest_kms_key/arn"
                            }
                        }
                    },
                    "Filter": {
                        "EligibleForReplication": True
                    },
                    "EnableManifestOutput": True
                }
            }
        }
    )


    ## Describe API
    describe_job = ApiCall(
        method = "list_jobs",
        method_args = {
            "AccountId": "$src_account",
            ## replication jobs fail after manifest is generated
            "JobStatuses": ["New", "Preparing", "Failed"]
        },
        ## jobs don't have ARNs, but pretend a JobId is an ARN
        output_keys = {
            "arn": f"Jobs/?/Description~{job_description}/JobId"
        }
    )
    def ignore_if_forced(forced=None):
        if forced:
            return {"arn": None}
    get_job_arn = Transformer(
        func = ignore_if_forced,
        function_args = {"forced": force},
        output_keys = ["arn"]
    )


    replication_job_resource = ResourceGroup(
        name = "src_batch_replication",
        type = "s3control",
        create_apis = (wait_for_lambda_and_rule, create_job),
        describe_apis = (describe_job, get_job_arn)
    )
    return replication_job_resource