from glob import glob
from invoke import task
from matplotlib.pyplot import savefig, subplots
from os import makedirs
from os.path import join
from pandas import read_csv
from pprint import pprint
from requests import post
from subprocess import run as sp_run
from tasks.util.env import (
    PROJ_ROOT,
    TLESS_PLOT_COLORS,
    TLESS_HATCH_STYLES,
    TLESS_MODES,
    get_faasm_root,
)
from tasks.util.faasm import (
    flush_hosts,
    get_faasm_invoke_host_port,
)
from time import sleep, time


FU_ROOT = join(PROJ_ROOT, "ffmpeg-ubench")


def _init_csv_file(mode, wload):
    result_dir = join(FU_ROOT, "data")
    makedirs(result_dir, exist_ok=True)

    csv_name = "fu_{}_{}.csv".format(mode, wload)
    csv_file = join(result_dir, csv_name)
    with open(csv_file, "w") as out_file:
        out_file.write("NumRun,TimeMs\n")


def _write_csv_line(mode, wload, num_run, time_elapsed):
    result_dir = join(FU_ROOT, "data")
    csv_name = "fu_{}_{}.csv".format(mode, wload)
    csv_file = join(result_dir, csv_name)
    with open(csv_file, "a") as out_file:
        out_file.write("{},{}\n".format(num_run, time_elapsed))


# def do_single_run(mode, wload, num_run):
#     """
#     Do a single run of the FFmpeg microbench and measure the time elapsed in
#     miliseconds
#     """
#     host, port = get_faasm_invoke_host_port()
#     url = "http://{}:{}".format(host, port)
#
#     # Post `np` asynchronous execution requests
#     cmdline = "file:faasm://tless/sample_video.mpeg file:faasm://tless/sample_video_out.mpeg"
#     msg = {
#         "user": "tless",
#         "function": wload if wload != "ffmpeg" else "transcode",
#         "cmdline": cmdline,
#     }
#     print("Posting to {} msg:".format(url))
#     pprint(msg)
#
#     start_time = time()
#     response = post(url, json=msg, timeout=None)
#     elapsed_time = time() - start_time
#     # Get the async message id
#     if response.status_code != 200:
#         print(
#             "WARNING: request failed: {}:\n{}".format(
#                 response.status_code, response.text
#             )
#         )
#         return
#
#     _write_csv_line(mode, wload, num_run, elapsed_time * 1000)


def _serialise_dict(d):
    """
    Helper function to serialise a dictionary into a string of env. variables
    """
    return " ".join(["{}={}".format(k, d[k]) for k in d])


def do_single_run(mode, wload, num_run):
    """
    Do a single run of the image processing pipeline and return the time
    elapsed in miliseconds
    """
    run_cmd = [
        "docker compose exec faasm-cli",
        "bash -c",
        "'{} /build/faasm/bin/func_runner tless {}'".format(
            _serialise_dict(TLESS_MODES[mode]), wload
        ),
    ]
    run_cmd = " ".join(run_cmd)
    print(run_cmd)
    start_time = time()
    sp_run(run_cmd, shell=True, check=True, cwd=get_faasm_root())
    elapsed_time = time() - start_time
    _write_csv_line(mode, wload, num_run, elapsed_time * 1000)
    return (time() - start_time) * 1e3


@task(default=True)
def run(ctx, mode=None, wl=None, repeats=10):
    """
    Run the FFmpeg micro benchmark in a confidential VM
    """
    if mode:
        modes = [mode]
    else:
        modes = list(TLESS_MODES.keys())
    if wl:
        workloads = [wl]
    else:
        workloads = ["noop", "ffmpeg", "noop-chain", "ffmpeg-chain"]

    # Run the experiment
    for _mode in modes:
        for wload in workloads:
            _init_csv_file(_mode, wload)

            for num in range(repeats):
                do_single_run(_mode, wload, num)
            sleep(2)


def _read_results():
    result_dict = {}
    result_dir = join(FU_ROOT, "data")

    for csv in glob(join(result_dir, "fu_*.csv")):
        workload = csv.split("_")[1]
        func = csv.split("_")[2][:-4]
        df = read_csv(csv)
        if workload not in result_dict:
            result_dict[workload] = {}
        result_dict[workload][func] = [
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
    plot_dir = join(FU_ROOT, "plot")
    makedirs(plot_dir, exist_ok=True)

    # fig, (ax1, ax2) = subplots(nrows=1, ncols=2, figsize=(6, 3))
    fig, ax = subplots(figsize=(6, 3))
    x = [1, 2, 3, 4, 5]
    funcs = ["noop", "noop-chain", "ffmpeg", "ffmpeg-chain"]
    w = 0.3
    for ind, workload in enumerate(results):
        xs = [_x + w*(ind - 0.5) for _x in x]
        ys = [results[workload][func][0] for func in funcs]
        ys_err = [results[workload][func][1] for func in funcs]

        ax.bar(
            xs,
            ys,
            width=w,
            yerr=ys_err,
            label="{}".format(workload if workload != "strawman" else "one-func-one-tee"),
            hatch=TLESS_HATCH_STYLES[ind],
            edgecolor="black",
        )

    ax.legend()
    ax.set_xticks([_ for _ in range(len(funcs))])
    ax.set_xticklabels(funcs)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    # ax.set_xlabel("Number of Inference Rounds")
    ax.set_ylabel("Time Elapsed [ms]")
    fig.tight_layout()
    savefig(join(plot_dir, "ffmpeg_ubench.pdf"), format="pdf")
