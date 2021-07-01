from .categories import (
    AR_OT_category_add,
    AR_OT_category_edit,
    AR_OT_category_interface,
    AR_OT_category_apply_visibility,
    AR_OT_category_delete_visibility,
    AR_OT_category_delete
)

from .globals import (
    AR_OT_gloabal_recategorize_action
)

from .locals import (
    AR_OT_local_to_global
)

from .preferences import(
    AR_OT_preferences_directory_selector,
    AR_OT_preferences_recover_directory
)

from .shared import (
    AR_OT_check_ctrl,
    AR_OT_open_url
)

def get_classes() -> list:
    from .categories import classes as categories_classes
    from .globals import classes as globals_classes
    from .locals import classes as locals_classes
    from .preferences import classes as preferences_classes
    from .shared import classes as shared_classes
    return categories_classes + globals_classes + locals_classes + preferences_classes + shared_classes

