from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User          # noqa: E402,F401
from .patient import Patient    # noqa: E402,F401
from .doctor import Doctor      # noqa: E402,F401
from .lab_order import LabOrder, LabOrderTest  # noqa: E402,F401
from .sample import Sample      # noqa: E402,F401
from .test_catalog import TestCatalog  # noqa: E402,F401
from .result import Result      # noqa: E402,F401
from .billing import Invoice, Payment  # noqa: E402,F401
from .inventory import InventoryItem, InventoryTransaction  # noqa: E402,F401
from .audit import AuditLog     # noqa: E402,F401
