from invoke import task
from tasks.util.faasm import flush_hosts


def _init_csv_file(m):
    result_dir = join(CDF_ROOT, "data")
    makedirs(result_dir, exist_ok=True)

    csv_name = "cdf_{}.csv".format(m)
    csv_file = join(result_dir, csv_name)
    with open(csv_file, "w") as out_file:
        out_file.write("NumRun,TimeMs\n")


@task
def run(ctx, parallel_pipelines=None):
    host, port = get_faasm_invoke_host_port()
    url = "http://{}:{}".format(host, port)

    # First, flush the host state
    flush_hosts()

    if parallel_pipelines:
        num_pipelines = [parallel_pipelines]
    else:
        num_pipelines = [1, 2, 3, 4, 5]


@task
def plot(ctx):
    pass
