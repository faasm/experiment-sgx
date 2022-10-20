from glob import glob
from invoke import task
from json import loads as json_loads
from os import makedirs
from os.path import join
from pandas import read_csv
from pprint import pprint
from requests import post
from subprocess import run as sp_run
from tasks.util.faasm import (
    flush_hosts,
    get_faasm_exec_time_from_json,
    get_faasm_invoke_host_port,
)
from tasks.util.env import (
    PROJ_ROOT,
    TLESS_LINE_STYLES,
    TLESS_PLOT_COLORS,
    get_faasm_root,
)
from time import sleep

import matplotlib.pyplot as plt

SS_ROOT = join(PROJ_ROOT, "strong-scaling")
NUM_NODES = 7
NUM_CORES_PER_NODE = 4
modes = {
    "tless": {
        "WASM_VM": "sgx",
        "AZ_ATESTATION_PROVIDER_URL": "https://faasmattprov.eus2.attest.azure.net",
        "ENCLAVE_ISOLATION_MODE": "global",
    },
    "tless-no-att": {
        "WASM_VM": "sgx",
        "AZ_ATTESTATION_PROVIDER_URL": "off",
        "ENCLAVE_ISOLATION_MODE": "global",
    },
    "faasm": {
        "WASM_VM": "wamr",
        "AZ_ATESTATION_PROVIDER_URL": "https://faasmattprov.eus2.attest.azure.net",
        "ENCLAVE_ISOLATION_MODE": "global",
    },
    "strawman": {
        "WASM_VM": "sgx",
        "AZ_ATESTATION_PROVIDER_URL": "https://faasmattprov.eus2.attest.azure.net",
        "ENCLAVE_ISOLATION_MODE": "faaslet",
    },
}


def _init_csv_file(m, np):
    result_dir = join(SS_ROOT, "data")
    makedirs(result_dir, exist_ok=True)

    csv_name = "ss_{}_{}.csv".format(m, np)
    csv_file = join(result_dir, csv_name)
    with open(csv_file, "w") as out_file:
        out_file.write("NumRun,TimeSec\n")


def _write_csv_line(m, np, num_run, time_sec):
    result_dir = join(SS_ROOT, "data")
    csv_name = "ss_{}_{}.csv".format(m, np)
    csv_file = join(result_dir, csv_name)
    with open(csv_file, "a") as out_file:
        out_file.write("{},{}\n".format(num_run, time_sec))


def do_single_run(mode, np, rep):
    """
    Run `np` pipelines concurrently. Issue `np` asynchronous execution requests
    and poll the messages until all of them have finished. Return the execution
    time for each of them.
    """
    host, port = get_faasm_invoke_host_port()
    url = "http://{}:{}".format(host, port)
    num_inference_rounds = 50
    msg_ids = set()

    # Post `np` asynchronous execution requests
    for _ in range(np):
        msg = {
            "user": "tless",
            "function": "pre",
            "cmdline": "{}".format(num_inference_rounds),
            "async": True,
        }
        print("Posting to {} msg:".format(url))
        pprint(msg)

        response = post(url, json=msg, timeout=None)
        # Get the async message id
        if response.status_code != 200:
            print(
                "Initial request failed: {}:\n{}".format(
                    response.status_code, response.text
                )
            )
        print("Response: {}".format(response.text))
        msg_ids.add(int(response.text.strip()))

        sleep(2)

    if len(msg_ids) != np:
        print("Error: have not gathered enough message ids")
        print("Expected: {} - Got: {}", np, len(msg_ids))
        raise RuntimeError("Not enough results")

    # Poll for the execution times
    poll_interval = 2
    while len(msg_ids) != 0:
        for msg_id in msg_ids:
            sleep(poll_interval)

            status_msg = {
                "user": "tless",
                "function": "pre",
                "status": True,
                "id": msg_id,
            }
            print("Posting to {} msg:".format(url))
            pprint(status_msg)
            response = post(url, json=status_msg)
            print("Response: {}".format(response.text))

            if response.text.startswith("RUNNING"):
                continue
            elif response.text.startswith("FAILED"):
                print("WARNING: Call failed!")
                msg_ids.remove(msg_id)
                break
            elif not response.text:
                print("WARNING: Empty response")
                msg_ids.remove(msg_id)
                break
            else:
                # First, get the result from the response text
                result_json = json_loads(response.text)
                _write_csv_line(
                    mode, np, rep, get_faasm_exec_time_from_json(result_json)
                )

                # If we reach this point it means the call has succeeded
                msg_ids.remove(msg_id)
                break

        print(
            "Waiting for: [{}]".format(",".join([str(mid) for mid in msg_ids]))
        )


@task(default=True)
def run(ctx, mode, pp=None, repeats=3):
    _init_csv_file(mode, pp)

    # First, flush the host state
    flush_hosts()

    # Experiment Parameters
    if pp:
        num_pipelines = [int(pp)]
    else:
        num_pipelines = [1, 2, 3, 4, 5]

    # Run the experiment
    for np in num_pipelines:
        for rep in range(repeats):
            exec_times = do_single_run(mode, np, rep)
            # for exec_time in exec_times:

        # Flush between different number of parallel pipelines
        flush_hosts()


@task()
def patch(ctx, mode="tless"):
    """
    Patch a kubernetes deployment for a system mode
    """
    k8s_files = join(get_faasm_root(), "deploy", "k8s-sgx")

    # First replace the WASM VM if necessary
    if mode == "faasm":
        wasm_vm_not = "sgx"
        wasm_vm = "wamr"
    else:
        wasm_vm_not = "wamr"
        wasm_vm = "sgx"
    find_cmd = [
        "find {}".format(k8s_files),
        "-type f",
        "| xargs sed -i",
        '\'s/value: "{}"/value: "{}"/g\''.format(wasm_vm_not, wasm_vm),
    ]
    find_cmd = " ".join(find_cmd)
    print(find_cmd)
    sp_run(find_cmd, shell=True, check=True)

    # Second replace the attestation service url
    if mode == "faasm":
        return
    elif mode == "tless-no-att":
        att_serv_not = "https://faasmattprov.eus2.attest.azure.net"
        att_serv = "off"
    find_cmd = [
        "find {}".format(k8s_files),
        "-type f",
        "| xargs sed -i",
        '\'s/value: "{}"/value: "{}"/g\''.format(wasm_vm_not, wasm_vm),
    ]
    find_cmd = " ".join(find_cmd)
    print(find_cmd)


def _load_results():
    result_dict = {}
    result_dir = join(SS_ROOT, "data")
    for csv in glob(join(result_dir, "ss_*.csv")):
        workload = csv.split("_")[1]
        np = csv.split("_")[2][:-4]
        df = read_csv(csv)
        if workload not in result_dict:
            result_dict[workload] = {}
        result_dict[workload][np] = [
            df["TimeSec"].mean(),
            df["TimeSec"].sem(),
        ]
    return result_dict


@task
def plot(ctx):
    results = _load_results()
    plot_dir = join(SS_ROOT, "plot")
    makedirs(plot_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 3))
    for ind, workload in enumerate(results):
        xs = list(results[workload].keys())
        xs.sort()
        ys = [results[workload][x][0] for x in xs]
        ys_err = [results[workload][x][1] for x in xs]

        ax.errorbar(
            [int(x) for x in xs],
            ys,
            yerr=ys_err,
            linestyle=TLESS_LINE_STYLES[ind],
            marker=".",
            label="{}".format(
                workload if workload != "strawman" else "one-func-one-tee"
            ),
            color=TLESS_PLOT_COLORS[ind],
        )

    ax.legend()
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Number of Concurrent Applications")
    ax.set_ylabel("Average Application Exec. Time [s]")
    fig.tight_layout()
    plt.savefig(join(plot_dir, "strong_scaling.pdf"), format="pdf")
