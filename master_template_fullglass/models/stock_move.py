# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class StockMove(models.Model):
	_inherit = 'stock.move'

