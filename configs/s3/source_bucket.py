SOURCE_BUCKET_POLICY_TEMPLATE = {
    "Sid": "CloudCopyCat-SourceObjectGet",
    "Effect": "Allow",
    "Principal": {
        "AWS": "$dest_copy_role/arn"
    },
    "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl",
        "s3:GetObjectTagging",
        "s3:GetObjectVersionAcl",
        "s3:GetObjectVersionTagging",
        "s3:*"
    ],
    "Resource": "$src_bucket/#id/object_arn"
}

## Don't overwrite source bucket policy, append to it!



EMPTY_BUCKET_POLICY_TEMPLATE = {
    "Version": "2012-10-17",
    "Statement": [
        SOURCE_BUCKET_POLICY_TEMPLATE
    ]
}
## In case there is no policy at all