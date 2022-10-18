from glob import glob
from invoke import task
from os import makedirs
from os.path import exists, join
from tasks.util.env import PROJ_ROOT, TLESS_PLOT_COLORS, TLESS_DATA_FILES, TLESS_FUNCTIONS, get_faasm_root
from subprocess import run as sp_run
from time import time

import matplotlib.pyplot as plt
import pandas as pd

CDF_ROOT = join(PROJ_ROOT, "cdf")


@task
def wasm(ctx):
    for f in TLESS_FUNCTIONS:
        user = f[0]
        func = f[1]

        wasm_file = join(PROJ_ROOT, "wasm", user, func, "function.wasm")
        faasm_path = join(
            get_faasm_root(), "dev", "faasm-local", "wasm", user, func
        )
        if not exists(faasm_path):
            # this does not work
            makedirs(faasm_path)

        cp_cmd = "cp {} {}".format(wasm_file, faasm_path)
        print(cp_cmd)
        run(cp_cmd, shell=True, check=True)


@task
def data(ctx):
    faasm_path_base = join(get_faasm_root(), "dev", "faasm-local", "shared", "tless")
    if not exists(faasm_path_base):
        # TODO: this does not work
        makedirs(faasm_path_base)
    for df in TLESS_DATA_FILES:
        host_path = df[0]
        faasm_path = join(faasm_path_base, df[1].split("/")[-1])
        cmd = "sudo cp {} {}".format(host_path, faasm_path)
        print(cmd)
        sp_run(cmd, shell=True, check=True)




def _init_csv_file(m):
    result_dir = join(CDF_ROOT, "data")
    makedirs(result_dir, exist_ok=True)

    csv_name = "cdf_{}.csv".format(m)
    csv_file = join(result_dir, csv_name)
    with open(csv_file, "w") as out_file:
        out_file.write("NumRun,TimeMs\n")


def _write_csv_line(m, num_run, time_elapsed):
    result_dir = join(CDF_ROOT, "data")
    csv_name = "cdf_{}.csv".format(m)
    csv_file = join(result_dir, csv_name)
    with open(csv_file, "a") as out_file:
        out_file.write("{},{}\n".format(num_run, time_elapsed))


def _serialise_dict(d):
    """
    Helper function to serialise a dictionary into a string of env. variables
    """
    return " ".join(["{}={}".format(k, d[k]) for k in d])


def do_single_run(env={}):
    """
    Do a single run of the image processing pipeline and return the time
    elapsed in miliseconds
    """
    run_cmd = [
        "docker compose exec faasm-cli",
        "bash -c",
        "'{} /build/faasm/bin/func_runner tless pre'".format(
            _serialise_dict(env)
        ),
    ]
    run_cmd = " ".join(run_cmd)
    print(run_cmd)
    start_time = time()
    sp_run(run_cmd, shell=True, check=True, cwd=get_faasm_root())
    return (time() - start_time) * 1e3


@task(default=True)
def run(ctx):
    """
    Run CDF-latency experiment
    """
    num_repeats = 3
    modes = {
        "tless": {},
        "tless-no-att": {"AZ_ATTESTATION_PROVIDER_URL": "off"},
        "faasm": {"WASM_VM": "wamr"},
    }

    # Run the experiment
    for m in modes:
        _init_csv_file(m)
        for num in range(num_repeats):
            _write_csv_line(m, num, do_single_run(modes[m]))


def _read_results():
    result_dict = {}
    result_dir = join(CDF_ROOT, "data")

    for csv in glob(join(result_dir, "cdf_*.csv")):
        workload = csv.split("_")[1][:-4]
        df = pd.read_csv(csv)
        result_dict[workload] = df["TimeMs"].to_list()

    return result_dict


@task
def plot(ctx):
    """
    Plot results
    """
    results = _read_results()
    plot_dir = join(CDF_ROOT, "plot")
    makedirs(plot_dir, exist_ok=True)

    n_bins = 100
    fig, ax = plt.subplots(figsize=(6, 3))
    for ind, workload in enumerate(results):
        ax.hist(
            results[workload],
            n_bins,
            density=True,
            cumulative=True,
            label="{}".format(workload),
            color=TLESS_PLOT_COLORS[ind],
        )

    ax.legend()
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0, top=1)
    ax.set_xlabel("Latency [ms]")
    ax.set_ylabel("CDF")
    fig.tight_layout()
    plt.savefig(join(plot_dir, "cdf.png"), format="png")
