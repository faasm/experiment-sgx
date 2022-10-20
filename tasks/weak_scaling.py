from glob import glob
from invoke import task
from json import loads as json_loads
from os import makedirs
from os.path import join
from pprint import pprint
from requests import post
from tasks.util.env import (
    PROJ_ROOT,
    TLESS_PLOT_COLORS,
    TLESS_LINE_STYLES,
)
from tasks.util.faasm import (
    flush_hosts,
    get_faasm_exec_time_from_json,
    get_faasm_invoke_host_port,
)
from time import sleep

import matplotlib.pyplot as plt
import pandas as pd

WS_ROOT = join(PROJ_ROOT, "weak-scaling")


def _init_csv_file(m, size):
    result_dir = join(WS_ROOT, "data")
    makedirs(result_dir, exist_ok=True)

    csv_name = "ws_{}_{}.csv".format(m, size)
    csv_file = join(result_dir, csv_name)
    with open(csv_file, "w") as out_file:
        out_file.write("NumRun,TimeMs\n")


def _write_csv_line(mode, size, num_run, time_elapsed):
    result_dir = join(WS_ROOT, "data")
    csv_name = "ws_{}_{}.csv".format(mode, size)
    csv_file = join(result_dir, csv_name)
    with open(csv_file, "a") as out_file:
        out_file.write("{},{}\n".format(num_run, time_elapsed))


def _serialise_dict(d):
    """
    Helper function to serialise a dictionary into a string of env. variables
    """
    return " ".join(["{}={}".format(k, d[k]) for k in d])


def do_single_run(mode, size, num_run):
    """
    Do a single run of the image processing pipeline and return the time
    elapsed in miliseconds
    """
    host, port = get_faasm_invoke_host_port()
    url = "http://{}:{}".format(host, port)

    # Post `np` asynchronous execution requests
    msg = {
        "user": "tless",
        "function": "pre",
        "cmdline": "{}".format(size),
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
    msg_id = int(response.text.strip())

    while True:
        sleep(2)
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
            break
        elif not response.text:
            print("WARNING: Empty response")
            break
        else:
            # First, get the result from the response text
            result_json = json_loads(response.text)
            _write_csv_line(
                mode, size, num_run, get_faasm_exec_time_from_json(result_json)
            )
            break


@task(default=True)
def run(ctx, mode, size=None, repeats=3):
    """
    Run the weak scaling experiment: scale the problem up
    """
    flush_hosts()
    if size:
        size_list = [size]
    else:
        size_list = [10, 20, 30, 40, 50]

    # Run the experiment
    for size in size_list:
        _init_csv_file(mode, size)

        for num in range(repeats):
            do_single_run(mode, size, num)
            sleep(5)

        flush_hosts()


def _read_results():
    result_dict = {}
    result_dir = join(WS_ROOT, "data")

    for csv in glob(join(result_dir, "ws_*.csv")):
        workload = csv.split("_")[1]
        size = csv.split("_")[2][:-4]
        df = pd.read_csv(csv)
        if workload not in result_dict:
            result_dict[workload] = {}
        result_dict[workload][size] = [
            df["TimeMs"].mean(),
            df["TimeMs"].sem(),
        ]

    return result_dict


@task
def plot(ctx):
    """
    Plot results
    """
    results = _read_results()
    plot_dir = join(WS_ROOT, "plot")
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
    ax.set_xlabel("Number of Inference Rounds")
    ax.set_ylabel("Time Elapsed [s]")
    fig.tight_layout()
    plt.savefig(join(plot_dir, "weak_scaling.pdf"), format="pdf")
