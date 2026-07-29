# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo.fields import Field
if not hasattr(Field, "ondelete"):
    Field.ondelete = None

from . import models
from . import controllers
from . import schemas
from . import routers
