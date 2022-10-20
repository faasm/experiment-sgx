from invoke import Collection

from . import attestation
from . import ffmpeg
from . import policy
from . import strong_scaling
from . import upload
from . import weak_scaling

ns = Collection(
    attestation,
    ffmpeg,
    policy,
    strong_scaling,
    upload,
    weak_scaling,
)
