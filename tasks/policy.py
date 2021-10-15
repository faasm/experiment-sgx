from invoke import task
from subprocess import run
from tasks.util.env import (
    AZURE_ATTESTATION_PROVIDER_NAME,
    AZURE_ATTESTATION_TYPE,
    AZURE_RESOURCE_GROUP,
)


def run_az_policy_cmd(action, az_args=None):
    cmd = [
        "az",
        "attestation policy {}".format(action),
        "--resource-group {}".format(AZURE_RESOURCE_GROUP),
        "--name {}".format(AZURE_ATTESTATION_PROVIDER_NAME),
        "--attestation-type {}".format(AZURE_ATTESTATION_TYPE),
    ]

    if az_args:
        cmd.extend(az_args)

    cmd = " ".join(cmd)
    print(cmd)
    run(cmd, shell=True, check=True)


@task
def show(ctx):
    """
    Show current attestation policy
    """
    run_az_policy_cmd("show")


@task
def set(ctx, file_path, jwt=False):
    """
    Set new attesation policy file
    """
    run_az_policy_cmd(
        "set",
        [
            "--new--attestation--policy-file {}".format(file_path),
            "--policy-format JWT" if jwt else "",
        ],
    )
