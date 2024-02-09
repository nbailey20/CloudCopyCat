## DO NOT EDIT THIS FILE

DEST_BUCKET_POLICY_TEMPLATE = {
    "Version": "2012-10-17",
    "Id": "",
    "Statement": [
        {
            "Sid": "Replication role object delivery",
            "Effect": "Allow",
            "Principal": {
                "AWS": "" ## to be filled in at deployment time
            },
            "Action": [
                "s3:ReplicateObject",
                "s3:ReplicateDelete",
                "s3:PutObject",
                "s3:*"
            ],
            "Resource": "" ## to be filled in at deployment time
        },
        {
            "Sid": "InventoryReportWrites",
            "Effect": "Allow",
            "Principal": {
                "Service": "s3.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": "", ## to be filled in at deployment time
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": "", ## to be filled in at deployment time
                    "s3:x-amz-acl": "bucket-owner-full-control"
                },
                "ArnLike": {
                    "aws:SourceArn": [] ## to be filled in at deployment time
                }
            }
        }
    ]
}

STATE_FILE_SCHEMA = {
    "awaiting_inv_report": [], ## To be filled in at deployment time
    "awaiting_batch_copy": [],
    "completed": {
        "successful": [],
        "error": []
    }
}
