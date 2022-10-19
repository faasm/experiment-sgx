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


## Run the experiments

Unfortunately, for each different mode we need a different kubernetes
deployment.

### TLess

First, deploy the TLess cluster:

```bash
cd ${FAASM_DIR}
source ./bin/workon.sh
inv k8s.deploy --workers=4 --sgx
```

To upload the data and WebAssembly required to run the image processing
pipelines, run:

```bash
cd ${EXP_SGX_DIR}
source ../../bin/workon.sh
inv upload.wasm upload.data
```

You can check that data has been successfully uploaded by navigating to the
`upload` pod on `k9s` and opening the logs (`l`).

Lastly, you can run the experiment with:

```bash
cd ${EXP_SGX_DIR}
source ../../bin/workon.sh
inv strong-scaling --mode tless
```

### Strawman

For the strawman solution, you just need to patch the TLess cluster:

```bash
kubectl set env -n faasm deployment/faasm-worker ENCLAVE_ISOLATION_MODE=faaslet
```

and run the experiment:

```bash
inv strong-scaling --mode strawman
```

### Faasm

First, deploy the TLess cluster, before doing so check that the files
`${FAASM_DIR}/deploy/k8s/upload.yml`

```bash
cd ${FAASM_DIR}
source ./bin/workon.sh
inv k8s.deploy --workers=4
```

To upload the data and WebAssembly required to run the image processing
pipelines, run:

```bash
cd ${EXP_SGX_DIR}
source ../../bin/workon.sh
inv upload.data upload.wasm
```

You can check that data has been successfully uploaded by navigating to the
`upload` pod on `k9s` and opening the logs (`l`).

Lastly, you can run the experiment with:

```bash
cd ${EXP_SGX_DIR}
source ../../bin/workon.sh
inv strong-scaling.run --mode tless
```

You can now delete the cluster:

```bash
cd ${FAASM_DIR}
inv k8s.delete
```

