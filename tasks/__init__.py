from invoke import Collection

from . import attestation
from . import weak_scaling
from . import policy
from . import upload

ns = Collection(
    attestation,
    policy,
    weak_scaling,
    upload,
)
