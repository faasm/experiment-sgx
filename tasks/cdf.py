from invoke import task
from os import makedirs
from os.path import join
from tasks.util.env import PROJ_ROOT, FAASM_ROOT_AZ_VM
from subprocess import run as sp_run
from time import time

CDF_ROOT = join(PROJ_ROOT, "cdf")


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
    sp_run(run_cmd, shell=True, check=True, cwd=FAASM_ROOT_AZ_VM)
    return (time() - start_time) * 1e3


@task(default=True)
def run(ctx):
    """
    Run CDF-latency experiment
    """
    num_repeats = 3
    modes = {
        "tless": {},
        "tless_no_att": {"AZ_ATTESTATION_PROVIDER_URL": "off"},
        "faasm": {"WASM_VM": "wamr"},
    }

    # Run the experiment
    for m in modes:
        _init_csv_file(m)
        for num in range(num_repeats):
            _write_csv_line(m, num, do_single_run(modes[m]))


@task
def plot(ctx):
    """
    Plot results
    """
    pass
