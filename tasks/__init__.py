from invoke import Collection

from . import attestation
from . import policy
from . import strong_scaling
from . import upload
from . import weak_scaling

ns = Collection(
    attestation,
    policy,
    strong_scaling,
    upload,
    weak_scaling,
)
