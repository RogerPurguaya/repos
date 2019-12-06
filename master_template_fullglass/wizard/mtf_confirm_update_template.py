# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class MtfConfirmUpdateTemplate(models.TransientModel):
	_name = 'mtf.confirm.update.template'

	template_id = fields.Many2one('mtf.template',required=True)
	current_sale_price = fields.Float('Actual Precio de venta',default=0.0)
	new_sale_price = fields.Float('Nuevo Precio de venta',default=0.0)

	def confirm(self):
		self.template_id.write(self._context.get('vals',{}))