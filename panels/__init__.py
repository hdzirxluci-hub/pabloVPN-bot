from database.models import Panel
from .base import BasePanel
from .marzban import MarzbanPanel
from .three_xui import ThreeXUIPanel
from .sanaei import SanaeiPanel
from .pasargad import PasargadPanel

def get_panel_adapter(panel: Panel) -> BasePanel:
    ptype = panel.panel_type.lower()
    if ptype == "marzban":
        return MarzbanPanel(panel)
    elif ptype == "3xui":
        return ThreeXUIPanel(panel)
    elif ptype == "sanaei":
        return SanaeiPanel(panel)
    elif ptype == "pasargad":
        return PasargadPanel(panel)
    else:
        raise ValueError(f"Unknown panel type: {ptype}")