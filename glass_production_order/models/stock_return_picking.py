# -*- coding: utf-8 -*-
from odoo import fields, models,api
from odoo.exceptions import UserError
from datetime import datetime

class StockReturnPicking(models.TransientModel):
	_inherit = 'stock.return.picking'

	@api.multi
	def create_returns(self):
		picking = self.env['stock.picking'].browse(self.env.context['active_id']).exists()
		# TDE FIXME Funcionalidad de devolución por desarrollar, esto se usará para prevenir corrupción de data...
		if picking.move_lines.mapped('glass_order_line_ids'):
			raise UserError('Se ha encontrado que el albarán %s contiene cristales en su demanda inicial, utilice la devolución por cristales para este tipo de extornos.')
		return super(StockReturnPicking,self).create_returns()