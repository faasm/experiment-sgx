from invoke import task
from tasks.util.env import (
    AZURE_RESOURCE_GROUP,
    AZURE_SGX_VM_SIZE,
    AZURE_SGX_LOCATION,
    AZURE_SGX_VM_IMAGE,
    AZURE_SGX_VM_NAME,
    AZURE_SGX_VM_ADMIN_USERNAME,
    AZURE_SGX_VM_SSH_KEY_FILE,
)
from subprocess import check_output, run


def _run_vm_cmd(name, az_args=None, capture_stdout=False):
    cmd = [
        "az",
        "vm {}".format(name),
        "--resource-group {}".format(AZURE_RESOURCE_GROUP),
    ]

    if az_args:
        cmd.extend(az_args)

    cmd = " ".join(cmd)
    print(cmd)
    if capture_stdout:
        return check_output(cmd, shell=True)
    else:
        run(cmd, shell=True, check=True)


def _run_del_network_cmd(name, suffix):
    cmd = [
        "az",
        "network {}".format(name),
        "delete",
        "--resource-group {}".format(AZURE_RESOURCE_GROUP),
        "--name {}{}".format(AZURE_SGX_VM_NAME, suffix),
    ]

    cmd = " ".join(cmd)
    print(cmd)
    run(cmd, shell=True, check=True)


@task
def provision(ctx):
    """
    Provision SGX-enabled VM
    """
    _run_vm_cmd(
        "create",
        [
            "--name {}".format(AZURE_SGX_VM_NAME),
            "--location {}".format(AZURE_SGX_LOCATION),
            "--image {}".format(AZURE_SGX_VM_IMAGE),
            "--size {}".format(AZURE_SGX_VM_SIZE),
            "--authentication-type ssh",
            "--public-ip-sku Standard",
            "--admin-username {}".format(AZURE_SGX_VM_ADMIN_USERNAME),
            "--generate-ssh-keys",
            "--ssh-key-values {}".format(AZURE_SGX_VM_SSH_KEY_FILE),
        ],
    )


def get_os_disk():
    out = _run_vm_cmd(
        "show",
        [
            "--name {}".format(AZURE_SGX_VM_NAME),
            "--query storageProfile.osDisk.managedDisk.id",
        ],
        capture_stdout=True,
    ).decode("utf-8")
    return out.split("/")[-1][:-2]


def get_ip():
    out = check_output(
        "az network public-ip show --resource-group {} --name {}PublicIp --query ipAddress".format(
            AZURE_RESOURCE_GROUP, AZURE_SGX_VM_NAME
        ),
        shell=True,
    )
    return out.decode("utf-8").strip().strip('"')


@task
def get_ssh(ctx):
    """
    Get the SSH config to log into the SGX VM
    """
    ssh_config = [
        "Host {}".format(AZURE_SGX_VM_NAME),
        "\n    HostName {}".format(get_ip()),
        "\n    User {}".format(AZURE_SGX_VM_ADMIN_USERNAME),
        "\n    ForwardAgent yes",
    ]
    print(" ".join(ssh_config))


@task
def delete(ctx):
    """
    Delete SGX VM
    """
    os_disk = get_os_disk()

    # Delete VM
    _run_vm_cmd(
        "delete",
        [
            "--name {}".format(AZURE_SGX_VM_NAME),
            "--yes",
        ],
    )

    # Delete OS disk
    run(
        "az disk delete --resource-group {} --name {} --yes".format(
            AZURE_RESOURCE_GROUP, os_disk
        ),
        shell=True,
    )

    # Network components to be deleted, order matters
    net_components = [
        ("nic", "VMNic"),
        ("nsg", "NSG"),
        ("vnet", "VNET"),
        ("public-ip", "PublicIp"),
    ]

    for name, suffix in net_components:
        _run_del_network_cmd(name, suffix)
