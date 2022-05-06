# SGX Experiments in Faasm

## Deploy an AKS cluster

```bash
inv cluster.provision --vm Standard_DC4s_v3 --nodes 4 --location eastus2 --sgx
inv cluster.credentials
```

Deploy the K8s cluster (TODO- automate)

```bash
inv knative.install # run twice
inv knative.deploy --replicas=4 --sgx # will fail in the worker step
kubectl apply -f ./deploy/k8s-sgx/worker_no_kn.yml
kubectl apply -f ./deploy/k8s-sgx/worker-lb.yml
```

Check that the SGX plugins are enabled:

```bash
# You should see both device and plugin stuff
kubectl get pods -n kube-system | grep sgx
```

Manually update IPs and ports in `faasm.ini`

```bash
kubctl -n faasm get service upload-lb
kubctl -n faasm get service worker-lb
```

## Deploy a fresh VM

First create the VM:

```
cd ~/experiment-base
source ./bin/workon.sh
inv vm.create --sgx --region eastus2
```

Then provision it:

```
inv vm.inventory --prefix faasm-sgx
# May have to comment out the linux-hwe-20.04 in ansible/tasks/base.yml`
inv vm.setup
```

SSH into the VM and then:

```
cd ~/code/faasm
./bin/cli.sh faasm-sgx
inv dev.cmake --sgx Hardware
```
