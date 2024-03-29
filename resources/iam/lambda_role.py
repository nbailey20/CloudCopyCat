LAMBDA_IAM_POLICY_TEMPLATE = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "logs:CreateLogGroup",
            "Effect": "Allow",
            "Resource": "" ## filled in at deployment time
        },
        {
            "Action": [
                "logs:PutLogEvents",
                "logs:CreateLogStream"
            ],
            "Effect": "Allow",
            "Resource": "" ## filled in at deployment time
        },
        {
            "Effect": "Allow",
            "Action": "s3:CreateJob",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "" ## filled in at deployment time
        },
        {
            "Effect": "Allow",
            "Action": "kms:*", ## TODO fine tune this
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "ssm:GetParameter",
            "Resource": "" ## filled in at deployment time
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "" ## filled in at deployment time
        }
    ]
}


LAMBDA_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}