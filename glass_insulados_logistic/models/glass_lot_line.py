# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class GlassLotLine(models.Model):
	_inherit = 'glass.lot.line'
	
	il_in_transfer = fields.Boolean('En transferencia')