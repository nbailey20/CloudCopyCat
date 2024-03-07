SOURCE_BUCKET_POLICY_TEMPLATE = {
    "Sid": "CloudCopyCat-SourceObjectGet",
    "Effect": "Allow",
    "Principal": {
        "AWS": "$dest_copy_role/arn"
    },
    "Action": [
        "s3:*"
    ],
    "Resource": "$src_bucket/#id/object_arn"
}

## Don't overwrite source bucket policy, append to it!



# "s3:GetObject",
# "s3:GetObjectVersion",
# "s3:GetObjectAcl",
# "s3:GetObjectTagging",
# "s3:GetObjectVersionAcl",
# "s3:GetObjectVersionTagging"