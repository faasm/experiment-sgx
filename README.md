# SGX Experiments in Faasm

Clone the [faasm/experiment-base](https://github.com/faasm/experiment-base) and
follow the instructions there to set up the repo structure (including this repo)
and your Azure account. You will also have to clone the main [faasm repo](
https://github.com/faasm/faasm).

For convinience, we export two env. variables:

```bash
export FAASM_EXP_BASE_DIR=<path/to/faasm/experiment-base>
export FAASM_DIR=<path/to/faasm/faasm>
```

## Deploy an AKS cluster

```bash
cd ${FAASM_EXP_BASE_DIR}
source ./bin/workon.sh
inv cluster.provision --vm Standard_DC4s_v3 --nodes 4 --location eastus2 --sgx
inv cluster.credentials
```

Deploy the Faasm cluster:

```bash
inv k8s.deploy --workers=4 --sgx
```

Check that the SGX plugins are enabled:

```bash
# You should see both device and plugin stuff
kubectl get pods -n kube-system | grep sgx
```

## Deploy a fresh VM

First create the VM:

```bash
cd ~/experiment-base
source ./bin/workon.sh
inv vm.create --sgx --region eastus2
```

Then provision it:

```bash
inv vm.inventory --prefix faasm-sgx
# May have to comment out the linux-hwe-20.04 in ansible/tasks/base.yml`
inv vm.setup
```

SSH into the VM and then:

```bash
cd ~/code/faasm
./bin/cli.sh faasm-sgx
inv dev.cmake --sgx Hardware
```

Note, if you want to fetch a branch different than master you may have to run:

```bash
cd ~/code/faasm
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
```

When you are done, delete the VM:

```bash
# List VMs and copy the relevant name (with sgx)
inv vm.list-all

inv vm.delete <vm_name>
```
