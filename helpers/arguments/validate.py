import subprocess
import re
from helpers.log import logger


def profile_exists(profile_name):
    try:
        sub_stdout = subprocess.run(
                        ["aws", "configure", "list-profiles"],
                        capture_output=True
                    ).stdout.strip()
        all_profiles = re.split(r"\s+", sub_stdout.decode("utf-8"))
    except Exception as err:
        logger.debug(f"Could not read available AWS CLI profiles: {err}")
        return False

    if profile_name in all_profiles:
        return True
    return False


def args_are_valid(args):
    if not profile_exists(args.src_profile):
        logger.debug(f"Source profile {args.src_profile} not found on system, aborting.")
        return False
    if not profile_exists(args.dest_profile):
        logger.debug(f"Destination profile {args.dest_profile} not found on system, aborting.")
        return False
    return True