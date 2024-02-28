SOURCE_BUCKET_POLICY_TEMPLATE = {
    "Sid": "CloudCopyCat-SourceObjectGet",
    "Effect": "Allow",
    "Principal": {
        "AWS": [] ## to be filled in
    },
    "Action": [
        "s3:*"
    ],
    "Resource": [] ## to be filled in
}

## Don't overwrite source bucket policy, append to it!



# "s3:GetObject",
# "s3:GetObjectVersion",
# "s3:GetObjectAcl",
# "s3:GetObjectTagging",
# "s3:GetObjectVersionAcl",
# "s3:GetObjectVersionTagging"