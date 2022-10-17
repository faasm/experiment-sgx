from invoke import Collection

from . import attestation
from . import cdf
from . import policy

ns = Collection(
    attestation,
    cdf,
    policy,
)
