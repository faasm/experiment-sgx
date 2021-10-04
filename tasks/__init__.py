from invoke import Collection

from . import attestation
from . import policy
from . import sgx
from . import vm

ns = Collection(
    attestation,
    policy,
    sgx,
    vm,
)
