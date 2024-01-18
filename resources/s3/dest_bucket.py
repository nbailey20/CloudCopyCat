## DO NOT EDIT THIS FILE

DEST_BUCKET_POLICY_TEMPLATE = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "InventoryReportWrites",
            "Effect": "Allow",
            "Principal": {
                "Service": "s3.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": [], ## To be filled in at deployment time
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": "", ## To be filled in at deployment time
                    "s3:x-amz-acl": "bucket-owner-full-control"
                },
                "ArnLike": {
                    "aws:SourceArn": [] ## To be filled in at deployment time
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