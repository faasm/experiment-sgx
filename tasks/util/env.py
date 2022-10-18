from os.path import dirname, expanduser, realpath, join
from socket import gethostname

PROJ_ROOT = dirname(dirname(dirname(realpath(__file__))))
FAASM_ROOT_AZ_VM = join(expanduser("~"), "code", "faasm")
FAASM_ROOT = join(expanduser("~"), "faasm")

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

# Plot aesthetics

TLESS_PLOT_COLORS = [
    (255 / 255, 162 / 255, 0 / 255),
    (62 / 255, 0 / 255, 161 / 255),
    (161 / 255, 0 / 255, 62 / 255),
    (0 / 255, 69 / 255, 22 / 255),
]

TLESS_FUNCTIONS = [
    ["tless", "pre"],
    ["tless", "imagemagick"],
    ["tless", "inference"],
    ["tless", "post_tf"],
    # ["tless", "post_im"],
]

# Path for TLess data in this repository
TLESS_DATA_DIR = join(PROJ_ROOT, "data")

# Path for TLess data to be uplodad in Faasm's filesystem
TLESS_FAASM_DATA_DIR = "/tless"

# For each data file, we have the origin path (where we copy data from), and
# the path in Faasm's filesystem we are gonna store the piece of data
TLESS_DATA_FILES = [
    [
        join(TLESS_DATA_DIR, "sample_image.png"),
        join(TLESS_FAASM_DATA_DIR, "sample_image_1.png"),
    ],
    [
        join(TLESS_DATA_DIR, "grace_hopper.bmp"),
        join(TLESS_FAASM_DATA_DIR, "grace_hopper.bmp"),
    ],
    [
        join(TLESS_DATA_DIR, "labels.txt"),
        join(TLESS_FAASM_DATA_DIR, "labels.txt"),
    ],
    [
        join(TLESS_DATA_DIR, "mobilenet_v1_1.0_224.tflite"),
        join(TLESS_FAASM_DATA_DIR, "mobilenet_v1.tflite"),
    ],
]


def get_faasm_root():
    if "koala" in gethostname():
        return FAASM_ROOT
    else:
        return FAASM_ROOT_AZ_VM
