from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_seasurf import SeaSurf
from flask_talisman import Talisman

# Initialize extensions
# Note: They will be properly initialized with app later using .init_app()
csrf = SeaSurf()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://",
)
talisman = Talisman()
