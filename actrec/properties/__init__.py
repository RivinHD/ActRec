from .categories import (
    AR_categories
)

from .globals import (
    AR_global_actions_enum
)

from .shared import (
    id_system,
    AR_macro,
    AR_action,
    data_manager
)

def get_classes() -> list:
    from .categories import classes as categories_classes
    from .globals import classes as globals_classes
    from .shared import classes as shared_classes
    return categories_classes + globals_classes + shared_classes
