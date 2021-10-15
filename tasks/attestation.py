from invoke import task
from subprocess import run
from tasks.util.env import (
    AZURE_ATTESTATION_PROVIDER_NAME,
    AZURE_RESOURCE_GROUP,
    AZURE_SGX_LOCATION,
)


def run_az_cmd(cmd):
    _cmd = "az {}".format(cmd)
    print(_cmd)
    run(_cmd, shell=True, check=True)


@task
def set_up(ctx):
    """
    Set up Azure Attestation Service extension (only needs to be done once)
    """
    run_az_cmd("extension add --name attestation")
    run_az_cmd("extension show --name attestation --query version")
    run_az_cmd("provider register --name Microsoft.Attestation")


def run_az_attestation_cmd(action, az_args=None):
    cmd = [
        "az",
        "attestation {}".format(action),
        "--resource-group {}".format(AZURE_RESOURCE_GROUP),
        "--name {}".format(AZURE_ATTESTATION_PROVIDER_NAME),
    ]

    if az_args:
        cmd.extend(az_args)

    cmd = " ".join(cmd)
    print(cmd)
    run(cmd, shell=True, check=True)


@task
def provider_create(ctx):
    """
    Create attestation provider
    """
    run_az_attestation_cmd(
        "create",
        [
            "--location {}".format(AZURE_SGX_LOCATION),
        ],
    )


@task
def provider_show(ctx):
    """
    Show attestation provider information
    """
    run_az_attestation_cmd("show")


@task
def provider_delete(ctx):
    """
    Delete attestation provider
    """
    run_az_attestation_cmd("delete")
