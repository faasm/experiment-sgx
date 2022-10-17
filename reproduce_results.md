# CDF of the latency to run the pipeline

## Provision IceLake VM

To create the VM, run:

```bash
cd ${EXPERIMENT_BASE}
source ./bin/workon.sh
inv vm.create --sgx --region eastus2
```

Record the command to access the VM using SSH.

Second, provision the VM using ansible:

```bash
inv vm.invnetory --prefix faasm-sgx
inv vm.setup
```

## Prepare the system

Then SSH into the VM and prepare the code:

```bash
<ssh with previous command>
cd code/faasm
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
cd faabric
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch origin && checkout not-track
cd ..
git checkout -b v<FAASM_TAG>
./bin/refresh_local.sh
./bin/cli.sh faasm-sgx
inv dev.cmake --sgx Hardware --build Release
inv dev.cc func_runner dev.cc codegen_func
```

## Prepare the WASM files and data

Place the WASM files and shared data:

```bash
TODO
```

Generate machine code for the different WASM functions in the experiment:

```bash
# First for TLess
inv \
  codegen tless imagemagick \
  codegen tless inference \
  codegen tless post_tf \
  codegen tless pre

# Then for the Faasm baseline
WASM_VM=wamr inv \
  codegen tless imagemagick \
  codegen tless inference \
  codegen tless post_tf \
  codegen tless pre
```

## Generate the results
