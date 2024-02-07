import json
import boto3

## Sample event received by Lambda

"""
{
    "version": "0",
    "id": "id#",
    "detail-type": "Object Created",
    "source": "aws.s3",
    "account": "account#",
    "time": "2023-12-18T01:21:53Z",
    "region": "us-east-1",
    "resources": [
        "arn:aws:s3:::bucketname"
    ],
    "detail": {
        "version": "0",
        "bucket": {
            "name": "bucketname"
        },
        "object": {
            "key": "CloudCopyCat-Data/bucketname/InvReport/2023-12-20T01-00Z/manifest.json",
            "size": 527,
            "etag": "c67405c5790bd2433561b54cd2ea47e3",
            "sequencer": "00657F9EB1A630B631"
        },
        "request-id": "id#",
        "requester": "s3.amazonaws.com",
        "source-ip-address": "10.0.28.72",
        "reason": "PutObject"
    }
}
"""

## State file schema
"""
{
    "awaiting_inv_report": [], ## To be filled in at deployment time
    "awaiting_batch_copy": [],
    "completed": {
        "successful": [],
        "error": []
    }
}
"""


def read_s3_object(bucket_name, object_path):
    client = boto3.client("s3")
    state_obj = client.get_object(
        Bucket = bucket_name,
        Key    = object_path
    )
    return json.loads(state_obj["Body"].read().decode("utf-8"))


def write_state_file(bucket_name, object_path, data):
    client = boto3.client("s3")
    client.put_object(
        Body   = bytes(json.dumps(data), encoding="utf-8"),
        Bucket = bucket_name,
        Key    = object_path
    )
    return


def get_ssm_param(param_name):
    client = boto3.client("ssm")
    param_val = client.get_parameter(
        Name           = param_name,
        WithDecryption = True
    )["Parameter"]["Value"]
    return param_val



def lambda_handler(event, _):
    print("Hi there")
    print(event)

    src_bucket_name  = event["detail"]["object"]["key"].split("/")[1]
    dest_bucket_name = event["detail"]["bucket"]["name"]

    state_path    = get_ssm_param("CloudCopyCat-State-File-Path")
    state         = read_s3_object(dest_bucket_name, state_path)
    manifest_path = event["detail"]["object"]["key"]
    manifest_type = manifest_path.split("/")[2]

    if manifest_type == "BatchCopy" and src_bucket_name in state["awaiting_batch_copy"]:
        manifest = read_s3_object(dest_bucket_name, manifest_path)
        ## ignore placeholder objects delivered to S3
        if manifest["Message"] and "This is a placeholder" in manifest["Message"]:
            print(f"Received placeholder message for {src_bucket_name}")
            return
        print(f"Batch copy complete for {src_bucket_name}")
        state["awaiting_batch_copy"].remove(src_bucket_name)
        ## TODO make sure all objects copied!
        state["completed"]["successful"].append(src_bucket_name)
        write_state_file(dest_bucket_name, state_path, state)

    elif manifest_type == "InvReport" and src_bucket_name in state["awaiting_inv_report"]:
        print(f"Creating batch copy for {src_bucket_name}")
        account_id     = event["account"]
        bucket_arn     = f"arn:aws:s3:::{dest_bucket_name}"
        object_arn     = f"{bucket_arn}/{event['detail']['object']['key']}"
        etag           = event["detail"]["object"]["etag"]
        batch_role_arn = get_ssm_param("CloudCopyCat-Batch-Role-Arn")

        client = boto3.client("s3control")
        job_id = client.create_job(
            AccountId            = account_id,
            ConfirmationRequired = False,
            Operation = {
                "S3PutObjectCopy": {
                    "TargetResource":  bucket_arn,
                    "StorageClass":    "STANDARD",
                    "TargetKeyPrefix": src_bucket_name
                }
            },
            Report = {
                "Bucket":      bucket_arn,
                "Format":      "Report_CSV_20180820",
                "Enabled":     True,
                "Prefix":      f"CloudCopyCat-Data/{src_bucket_name}/BatchCopy",
                "ReportScope": "AllTasks"
            },
            #ClientRequestToken="string",
            Manifest = {
                "Spec": {
                    "Format": "S3InventoryReport_CSV_20161130",
                },
                "Location": {
                    "ObjectArn": object_arn,
                    "ETag":      etag
                }
            },
            Priority = 10,
            RoleArn  = batch_role_arn
        )["JobId"]

        print(f"Created Job ID {job_id}")
        state["awaiting_inv_report"].remove(src_bucket_name)
        state["awaiting_batch_copy"].append(src_bucket_name)
        write_state_file(dest_bucket_name, state_path, state)

    else:
        print("Received unexpected event")
        print(state)
        print(event)

    print("Done.")
    return