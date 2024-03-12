#!/usr/bin/python3

import argparse
from rich_argparse import RichHelpFormatter

def parse_args():
    parser = argparse.ArgumentParser(
        prog            ="cloudcopycat",
        description     ="Move AWS data from one account to another.",
        epilog          ="",
        formatter_class = RichHelpFormatter
    )

    ## Add mandatory arguments
    mandatory = parser.add_argument_group("Required Arguments")
    mandatory.add_argument(
        "-sp", 
        "--source-profile",
        dest     ="src_profile",
        help     = "Profile in AWS credentials file for source account",
        required = True
    )
    mandatory.add_argument(
        "-dp", 
        "--dest-profile",
        dest     ="dest_profile",
        help     = "Profile in AWS credentials file for destination account",
        required = True
    )
    mandatory.add_argument(
        "-db", 
        "--dest-bucket",
        dest     ="dest_bucket",
        help     = "Destination bucket name where source account data should be copied to",
        required = True
    )
    mandatory.add_argument(
        "-e", 
        "--notify-email",
        dest     ="email",
        help     = "Email address to receive completion/error SNS notifications",
        required = True
    )

    ## Add optional arguments
    parser.add_argument(
        "--remove",
        dest   = "remove",
        action = "store_true",
        help   = "Remove an existing CloudCopyCat deployment (used after data copying is completed)"
    )
    parser.add_argument(
        "-r", 
        "--region",
        dest    = "region",
        help    = "Region to copy data from (default *)",
        default = "*"
    )
    parser.add_argument(
        "-sb", 
        "--source-bucket",
        dest    = "src_bucket",
        help    = "S3 Bucket name to copy data from (default *)",
        default = "*"
    )
    parser.add_argument( 
        "--force",
        dest   = "force",
        action = "store_true",
        help   = "Force CloudCopyCat to copy objects, even if Batch Copy jobs were previously created"
    )

    # Add verbosity flag
    parser.add_argument(
        "-v", 
        "--verbose", 
        dest   ="debug", 
        action ="store_true", 
        help   ="Display verbose output"
    )

    args = parser.parse_args()
    return args