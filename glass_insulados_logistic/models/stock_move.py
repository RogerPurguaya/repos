# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class StockMove(models.Model):
	_inherit = 'stock.move'

	mtf_requeriment_line_id = fields.Many2one('mtf.requisition.line',string=u'Línea de requisición de ficha')

