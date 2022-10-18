from invoke import Collection

from . import attestation
from . import cdf
from . import policy
from . import upload

ns = Collection(
    attestation,
    cdf,
    policy,
    upload,
)
