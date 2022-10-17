from invoke import Collection

from . import attestation
from . import cdf
from . import policy
from . import run
from . import sgx
from . import upload
from . import vm

ns = Collection(
    attestation,
    cdf,
    policy,
    run,
    sgx,
    upload,
    vm,
)
