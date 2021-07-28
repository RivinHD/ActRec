"""used by intra-modules: preferences, operators"""

from .categories import (
    AR_categories
)

from .globals import (
    AR_global_actions,
    AR_global_import_category,
    AR_global_export_categories
)

from .locals import (
    AR_local_actions,
    AR_local_load_text
)

from .shared import (
    id_system,
    AR_macro,
    AR_action,
    AR_scene_data
)

def get_classes() -> list:
    from .categories import classes as categories_classes
    from .globals import classes as globals_classes
    from .locals import classes as local_classes
    from .shared import classes as shared_classes
    return categories_classes + globals_classes + local_classes + shared_classes
