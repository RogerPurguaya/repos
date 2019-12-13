# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class StockMove(models.Model):
	_inherit = 'stock.move'

	@api.multi
	def action_cancel(self):
		res = super(StockMove,self).action_cancel()
		self.mapped('glass_order_line_ids').filtered(lambda l: l.lot_line_id.il_in_transfer).write({'il_in_transfer':False})
		return res
