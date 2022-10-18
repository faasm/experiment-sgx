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
inv vm.inventory --prefix faasm-sgx
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

# The following two commands will pull docker images, which will take a while
./bin/refresh_local.sh
./bin/cli.sh faasm-sgx

# The code build can also take some time
inv dev.cmake --sgx Hardware --build Release
inv dev.cc func_runner dev.cc codegen_func
```

## Prepare the WASM files and data

Place the WASM files and shared data:

```bash
cd ~/code/experiment-base/experiments/sgx
source ../../bin/workon.sh
source ./bin/workon.sh
# TODO: this does not create the directories properly
inv cdf.wasm
inv cdf.data
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

To generate the results, run:

```bash
inv cdf
```

and you may plot them with

```bash
inv cdf.plot
```

This will generate a `.png` image in [./cff/plot/cdf.png](./plot/cdf.png).
