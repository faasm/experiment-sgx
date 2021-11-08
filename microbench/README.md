# SGX Microbenchmarks

The set of microbenchmarks uses the `microbench_runner` in Faasm.

To execute locally, follow the instructions in the [faasm/experiment-microbench]
(https://github.com/faasm/experiment-microbench#local-faasm-set-up) repo.

Then, from `FAASM_ROOT` generate the machine code for the microbenchmark:

```
inv codegen demo hello --wamr --sgx
```

TODO: execute remotely?
