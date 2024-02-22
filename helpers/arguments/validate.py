import subprocess
import re

def profile_exists(profile_name):
    try:
        sub_stdout = subprocess.run(
                        ["aws", "configure", "list-profiles"],
                        capture_output=True
                    ).stdout.strip()
        all_profiles = re.split(r"\s+", sub_stdout.decode("utf-8"))
    except Exception as err:
        print(f"Could not read available AWS CLI profiles: {err}")
        return False

    if profile_name in all_profiles:
        return True
    return False


def args_are_valid(args):
    if not profile_exists(args.src_profile):
        print(f"Source profile {args.src_profile} not found on system, aborting.")
        return False
    if not profile_exists(args.dest_profile):
        print(f"Destination profile {args.dest_profile} not found on system, aborting.")
        return False
    return True