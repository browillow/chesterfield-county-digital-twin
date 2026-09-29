"""Generate transport types from the actual API without opening runtime stores."""

import json
from pathlib import Path

from chesterfield_twin.api.app import create_app
from chesterfield_twin.domain.contracts import Bootstrap

if __name__ == "__main__":
    app = create_app(bootstrap=Bootstrap)
    Path("openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n")
