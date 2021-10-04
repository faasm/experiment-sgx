from os.path import dirname, realpath, join

PROJ_ROOT = dirname(dirname(dirname(realpath(__file__))))

BIN_DIR = join(PROJ_ROOT, "bin")

SGX_INSTALL_DIR = "/opt/intel"

# Note that this is copied from faasm/experiment-base/tasks/util/env.py
AZURE_RESOURCE_GROUP = "faasm"

# SGX VM config

AZURE_SGX_VM_SIZE = "Standard_DC2ds_v3"
AZURE_SGX_LOCATION = "eastus2"
AZURE_SGX_VM_NAME = "faasm-sgx-vm"
AZURE_SGX_VM_IMAGE = "Canonical:UbuntuServer:18_04-lts-gen2:18.04.202109180"
AZURE_SGX_VM_ADMIN_USERNAME = "faasm"
AZURE_SGX_VM_SSH_KEY_FILE = "{}/experiments/sgx/pkeys".format(PROJ_ROOT)

# Attestation config

AZURE_ATTESTATION_PROVIDER_NAME = "faasmattprov"
AZURE_ATTESTATION_TYPE = "SGX-IntelSDK"
