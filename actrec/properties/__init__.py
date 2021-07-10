"""used by intra-modules: preferences, operators"""

from .categories import (
    AR_categories
)

from .globals import (
    AR_global_actions_enum,
    AR_global_import_category,
    AR_global_export_categories
)

from .shared import (
    id_system,
    AR_macro,
    AR_action
)

def get_classes() -> list:
    from .categories import classes as categories_classes
    from .globals import classes as globals_classes
    from .shared import classes as shared_classes
    return categories_classes + globals_classes + shared_classes
