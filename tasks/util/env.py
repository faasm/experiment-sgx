from os.path import dirname, realpath, join

PROJ_ROOT = dirname(dirname(dirname(realpath(__file__))))

BIN_DIR = join(PROJ_ROOT, "bin")

SGX_INSTALL_DIR = "/opt/intel"
