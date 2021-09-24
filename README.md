# SGX Experiments in Faasm

## Quick start from fresh VM

Install the required dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-invoke python3-pip
```

Initialise the virtual environment:
```bash
source ./bin/workon.sh
```

Now configure the APT repos:
```bash
sudo inv sgx.configure
```

Install the remaining dependencies:
```bash
sudo apt update && sudo apt install -y \
    az-dcap-client \
    dkms \
    libsgx-quote-ex \
    libsgx-enclave-common \
    libsgx-enclave-common-dev \
    libsgx-dcap-ql \
    libsgx-dcap-ql-dev \
    libssl-dev
```

Finally, install the DCAP driver and SGX SDK:
```bash
inv sgx.install
```

And source your environment:
```bash
source ~/.bashrc
```
