from invoke import task
from json import loads as json_loads
from os import makedirs
from os.path import exists, join
from pprint import pprint
from requests import post, put
from tasks.util.faasm import (
    fetch_latest_wasm,
    flush_hosts,
    get_faasm_exec_time_from_json,
    get_faasm_invoke_host_port,
    get_faasm_upload_host_port,
)
from tasks.util.env import (
    PROJ_ROOT,
    TLESS_DATA_FILES,
    TLESS_FUNCTIONS,
)
from time import sleep

SS_ROOT = join(PROJ_ROOT, "strong-scaling")
NUM_NODES = 7
NUM_CORES_PER_NODE = 4
modes = {
    "tless": {},
    "tless-no-att": {"AZ_ATTESTATION_PROVIDER_URL": "off"},
    "faasm": {"WASM_VM": "wamr"},
    "strawman": {"ENCLAVE_ISOLATION_MODE": "faaslet"},
}


@task()
def wasm(ctx, user_in=None, fetch=False):
    """
    Upload the Webassembly files for the TLess image processing pipeline. You
    can fetch the latest version from the toolchain repo using sudo and --fetch
    """
    host, port = get_faasm_upload_host_port()
    for f in TLESS_FUNCTIONS:
        if user_in:
            user = f[0]
        else:
            user = f[0]
        func = f[1]
        if fetch:
            fetch_latest_wasm(user, func)

        wasm_file = join(PROJ_ROOT, "wasm", user, func, "function.wasm")
        if not exists(wasm_file):
            print("Can not find wasm file: {}".format(wasm_file))
            print("Consider running with `--fetch`: `inv upload.wasm --fetch`")
            raise RuntimeError("WASM function not found")
        url = "http://{}:{}/f/{}/{}".format(host, port, user, func)
        print("Putting function to {}".format(url))
        response = put(url, data=open(wasm_file, "rb"))
        print("Response {}: {}".format(response.status_code, response.text))


@task
def data(ctx):
    """
    Upload the auxiliary data files for the TLess image processing pipeline
    """
    host, port = get_faasm_upload_host_port()
    url = "http://{}:{}/file".format(host, port)

    for df in TLESS_DATA_FILES:
        host_path = df[0]
        faasm_path = df[1]

        if not exists(host_path):
            print("Did not find data at {}".format(host_path))
            raise RuntimeError("Did not find data file")

        print(
            "Uploading TLess data ({}) to {} ({})".format(
                host_path, url, faasm_path
            )
        )
        response = put(
            url,
            data=open(host_path, "rb"),
            headers={"FilePath": faasm_path},
        )

        print("Response {}: {}".format(response.status_code, response.text))


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


def do_single_run(np):
    """
    Run `np` pipelines concurrently. Issue `np` asynchronous execution requests
    and poll the messages until all of them have finished. Return the execution
    time for each of them.
    """
    host, port = get_faasm_invoke_host_port()
    url = "http://{}:{}".format(host, port)
    num_inference_rounds = 50
    msg_ids = set()
    exec_times = []

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

    if len(msg_ids) != np:
        print("Error: have not gathered enough message ids")
        print("Expected: {} - Got: {}", np, len(msg_ids))
        raise RuntimeError("Not enough results")


    # Poll for the execution times
    poll_interval = 2
    while len(exec_times) != np:
        for msg_id in msg_ids:
            sleep(poll_interval)

            status_msg = {
                "user": "tless",
                "function": "pre",
                "status": True,
                "id": msg_id,
            }
            response = post(url, json=status_msg)

            if response.text.startswith("FAILED"):
                raise RuntimeError("Call failed")
            elif not response.text:
                raise RuntimeError("Empty status response")
            else:
                # First, get the result from the response text
                result_json = json_loads(response.text)
                exec_times.append(get_faasm_exec_time_from_json(result_json))

                # If we reach this point it means the call has succeeded
                msg_ids.remove(msg_id)

        print("Waiting for: [{}]".format(",".join(list(msg_ids))))

    # Finally, return the execution times
    return exec_times


@task
def run(ctx, mode="tless", parallel_pipelines=None):
    # First, flush the host state
    flush_hosts()

    # Experiment Parameters
    if parallel_pipelines:
        num_pipelines = [parallel_pipelines]
    else:
        num_pipelines = [1, 2, 3, 4, 5]
    # Do we need more than one repeat if we are already doing the average?
    num_repeats = 3

    # Run the experiment
    for np in num_pipelines:
        for rep in range(num_repeats):
            exec_times = do_single_run(np)
            for exec_time in exec_times:
                _write_csv_line(mode, np, rep, exec_time)


@task
def plot(ctx):
    pass
