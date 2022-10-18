# Strong-Scaling Experiment

## Provision the Kubernetes Cluster with IceLake Machines

To create the cluster, run:

```bash
cd ${FAASM_EXP_BASE_DIR}
source ./bin/workon.sh
inv cluster.provision --vm Standard_DC4s_v3 --nodes 4 --location eastus2 --sgx
inv cluster.credentials
```

Then, deploy the cluster:

```bash
cd ${FAASM_DIR}
source ./bin/workon.sh
inv k8s.deploy --workers=4 --sgx
```

You may open the `k9s` tool to monitor the cluster:

```bash
k9s
```

## Upload data and functions to the Kubernetes cluster

To upload the data and WebAssembly required to run the image processing
pipelines, run:

```bash
cd ${EXP_SGX_DIR}
source ../../bin/workon.sh
inv strong-scaling.data
inv strong-scaling.wasm
```
