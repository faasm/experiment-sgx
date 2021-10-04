from invoke import task
from requests import get
from subprocess import check_output, run
from tasks.util.env import BIN_DIR, SGX_INSTALL_DIR
import os


def do_configure(repo_url, write_file, key_url):
    # Modify the sources list
    with open("/etc/apt/sources.list.d/{}.list".format(write_file), "w+") as f:
        f.write("deb [arch=amd64] {} bionic main\n".format(repo_url))

    # Add key
    run("apt-key adv --fetch-keys {}".format(key_url), shell=True)


@task
def configure():
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
    run("chmod a+x {}".format(full_path), shell=True)

    # Run
    run(full_path)

def dcap_driver_installed():
    r = run("lsmod | grep intel_sgx", shell=True)
    return r.returncode == 0

def clone_azure_attestation_repo():
    run("rm -rf /opt/maa", shell=True)
    run("git clone https://github.com/Azure-Samples/microsoft-azure-attestation.git /opt/maa", shell=True)

@task
def install_dcap():
    print("Installing Intel SGX DCAP driver...")
    do_install(
        "https://download.01.org/intel-sgx/sgx-dcap/1.9/linux/distro/ubuntu18.04-server/sgx_linux_x64_driver_1.36.2.bin",
        "sgx_linux_x64_driver.bin",
    )


@task
def install_sgxsdk():
    print("Installing Intel SGX SDK...")
    run("mkdir /opt/intel", shell=True) #ensure directory exists
    do_install(
        "https://download.01.org/intel-sgx/sgx-dcap/1.9/linux/distro/ubuntu18.04-server/sgx_linux_x64_sdk_2.12.100.3.bin",
        "sgx_linux_x64_sdk.bin",
    )

    # Update .bashrc
    with open("/home/faasm/.bashrc", "a") as f:
        f.write("source {}/sgxddk/environment\n".format(SGX_INSTALL_DIR))

@task
def install_net_core_sdk():
    run("apt update", shell=True)
    run("apt install -y dotnet-sdk-3.1", shell=True)

@task
def install():
    if dcap_driver_installed():
        print("DCAP Driver installed. Skipping installation!")
    else:
        install_dcap()

    if os.path.isfile('/opt/intel/sgxsdk/environment'):
        print("SGX SDK installed. Skipping installation!")
    else:
        install_sgxsdk()
    install_net_core_sdk()
    clone_azure_attestation_repo()

@task
def generate_quotes():
    run("cd /opt/maa/intel.sdk.attest.sample/genquotes && AZDCAP_DEBUG_LOG_LEVEL=INFO bash ./runall.sh", shell=True)

#verifies quotes with the MAA
@task
def verify_quotes():
    run("cd /opt/maa/intel.sdk.attest.sample/validatequotes.core && bash ./runall.sh", shell=True)

@task
def demo():
    generate_quotes()
    verify_quotes()
