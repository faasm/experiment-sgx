from configparser import ConfigParser
from pprint import pprint
from os import makedirs
from os.path import expanduser, join, exists
from subprocess import run
from tasks.util.env import PROJ_ROOT, get_faasm_root

import requests
import time

FAASM_INI_FILE = join(expanduser("~"), ".config", "faasm.ini")
MESSAGE_TYPE_FLUSH = 3


def get_faasm_ini_value(section, key):
    if not exists(FAASM_INI_FILE):
        print("Expected to find faasm config at {}".format(FAASM_INI_FILE))
        raise RuntimeError("Did not find faasm config")

    config = ConfigParser()
    config.read(FAASM_INI_FILE)
    return config[section].get(key, "")


def get_faasm_upload_host_port():
    host = get_faasm_ini_value("Faasm", "upload_host")
    port = get_faasm_ini_value("Faasm", "upload_port")

    print("Using faasm upload {}:{}".format(host, port))
    return host, port


def get_faasm_invoke_host_port():
    host = get_faasm_ini_value("Faasm", "invoke_host")
    port = get_faasm_ini_value("Faasm", "invoke_port")

    print("Using faasm invoke {}:{}".format(host, port))
    return host, port


def get_faasm_worker_pods():
    pods = get_faasm_ini_value("Faasm", "worker_names")
    pods = [p.strip() for p in pods.split(",") if p.strip()]

    print("Using faasm worker pods: {}".format(pods))
    return pods


def get_faasm_exec_time_from_json(result_json):
    """
    Return the execution time (included in Faasm's response JSON) in seconds
    """
    actual_time = (
        float(int(result_json["finished"]) - int(result_json["timestamp"]))
        / 1000
    )

    return actual_time


def fetch_latest_wasm(user, func):
    wasm_path = join(
        get_faasm_root(),
        "dev",
        "faasm-local",
        "wasm",
        user,
        func,
        "function.wasm",
    )
    exp_wasm_path = join(PROJ_ROOT, "wasm", user, func)
    if not exists(wasm_path):
        print("WASM path does not exist: {}".format(wasm_path))
        raise RuntimeError("WASM file not found")
    if not exists(exp_wasm_path):
        makedirs(exp_wasm_path)

    cp_cmd = "cp {} {}".format(wasm_path, join(exp_wasm_path, "function.wasm"))
    print(cp_cmd)
    run(cp_cmd, shell=True, check=True)


def flush_hosts():
    # Prepare URL and headers
    host, port = get_faasm_invoke_host_port()
    url = "http://{}:{}".format(host, port)

    # Prepare message
    msg = {"type": MESSAGE_TYPE_FLUSH}
    print("Flushing functions, state, and shared files from workers")
    print("Posting to {} msg:".format(url))
    pprint(msg)
    response = requests.post(url, json=msg, timeout=None)
    if response.status_code != 200:
        print(
            "Flush request failed: {}:\n{}".format(
                response.status_code, response.text
            )
        )
    print("Waiting for flush to propagate...")
    time.sleep(5)
    print("Done waiting")