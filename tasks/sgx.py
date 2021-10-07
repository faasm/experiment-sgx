from invoke import task
from os import environ
from os.path import isfile
from requests import get
from shutil import rmtree
from subprocess import check_output, run
from tasks.util.env import BIN_DIR, SGX_INSTALL_DIR

MAA_DEMO_DIR = "/opt/maa"


def do_configure(repo_url, write_file, key_url):
    # Modify the sources list
    with open("/etc/apt/sources.list.d/{}.list".format(write_file), "w+") as f:
        f.write("deb [arch=amd64] {} bionic main\n".format(repo_url))

    # Add key
    run("apt-key adv --fetch-keys {}".format(key_url), shell=True)


@task
def configure(ctx):
    """
    Configure Intel and Microsoft APT repos
    """
    # Configure Intel APT repo
    do_configure(
        "https://download.01.org/intel-sgx/sgx_repo/ubuntu",
        "intel-sgx",
        "https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key",
    )

    # Configure Microsoft APT repo
    do_configure(
        "https://packages.microsoft.com/ubuntu/18.04/prod",
        "msprod",
        "https://packages.microsoft.com/keys/microsoft.asc",
    )


def do_install(url, fname):
    # Download binary
    r = get(url)
    full_path = "{}/{}".format(SGX_INSTALL_DIR, fname)
    with open(full_path, "wb+") as f:
        f.write(r.content)

    # Make executable
    run("chmod a+x {}".format(full_path), check=True, shell=True)

    # Run
    run(full_path)


def is_driver_installed(driver):
    if driver == "dcap":
        r = run("lsmod | grep intel_sgx", shell=True, check=True)
        return r.returncode == 0
    elif driver == "sgx":
        return isfile("/opt/intel/sgxsdk/environment")
    else:
        raise RuntimeError(
            "Don't know how to check if driver '{}' is installed".format(
                driver
            )
        )


def clone_azure_attestation_repo():
    rmtree(MAA_DEMO_DIR)
    run(
        "git clone https://github.com/Azure-Samples/microsoft-azure-attestation.git {}".format(
            MAA_DEMO_DIR
        ),
        shell=True,
        check=True,
    )


def install_dcap():
    print("Installing Intel SGX DCAP driver...")
    do_install(
        "https://download.01.org/intel-sgx/sgx-dcap/1.9/linux/distro/ubuntu18.04-server/sgx_linux_x64_driver_1.36.2.bin",
        "sgx_linux_x64_driver.bin",
    )


def install_sgxsdk():
    print("Installing Intel SGX SDK...")
    run(
        "mkdir -p /opt/intel", check=True, shell=True
    )  # ensure directory exists
    do_install(
        "https://download.01.org/intel-sgx/sgx-dcap/1.9/linux/distro/ubuntu18.04-server/sgx_linux_x64_sdk_2.12.100.3.bin",
        "sgx_linux_x64_sdk.bin",
    )

    # Update .bashrc
    with open("/home/faasm/.bashrc", "a") as f:
        f.write("source {}/sgxddk/environment\n".format(SGX_INSTALL_DIR))


def install_net_core_sdk():
    run("apt update", shell=True, check=True)
    run("apt install -y dotnet-sdk-3.1", shell=True, check=True)


@task
def install(ctx):
    """
    Install SGX drivers
    """
    if is_driver_installed("dcap"):
        print("DCAP Driver installed. Skipping installation!")
    else:
        install_dcap()

    if is_driver_installed("sgx"):
        print("SGX SDK installed. Skipping installation!")
    else:
        install_sgxsdk()
    install_net_core_sdk()
    clone_azure_attestation_repo()


def demo_generate_quotes():
    new_env = environ.copy()
    new_env["AZDCAP_DEBUG_LOG_LEVEL"] = "info"

    run(
        "bash ./runall.sh",
        cwd="{}/intel.sdk.attest.sample/genquotes".format(MAA_DEMO_DIR),
        shell=True,
        check=True,
        env=new_env,
    )


# verifies quotes with the MAA
def demo_verify_quotes():
    run(
        "cd /opt/maa/intel.sdk.attest.sample/validatequotes.core && bash ./runall.sh",
        shell=True,
        check=True,
    )


@task
def demo(ctx):
    """
    Run demo attestation validation
    """
    demo_generate_quotes()
    demo_verify_quotes()
