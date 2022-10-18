from invoke import task
from os.path import exists, join
from requests import put
from tasks.util.env import PROJ_ROOT, TLESS_DATA_FILES, TLESS_FUNCTIONS
from tasks.util.faasm import get_faasm_upload_host_port, fetch_latest_wasm


@task()
def wasm(ctx, fetch=False):
    """
    Upload the Webassembly files for the TLess image processing pipeline. You
    can fetch the latest version from the toolchain repo using sudo and --fetch
    """
    host, port = get_faasm_upload_host_port()
    for f in TLESS_FUNCTIONS:
        user = f[0]
        func = f[1]
        if fetch:
            fetch_latest_wasm(user, func)

        wasm_file = join(PROJ_ROOT, "wasm", user, func, "function.wasm")
        if not exists(wasm_file):
            print("Can not find wasm file: {}".format(wasm_file))
            print("Consider running with `--fetch`: `inv upload.wasm --fetch`")
            raise RuntimeError("WASM function not found")
        url = "http://{}:{}/f/{}/{}".format(
            host, port, user, func
        )
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

        print(
            "Response {}: {}".format(response.status_code, response.text)
        )
