# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError

class BuildGlassOrderWizard(models.TransientModel):
	_inherit = 'build.glass.order.wizard'

	def _prepare_glass_line_vals(self,vals):
		vals = super(BuildGlassOrderWizard,self)._prepare_glass_line_vals(vals)
		calc_line = self.env['glass.sale.calculator.line'].browse(vals.get('calc_line_id'))
		extra_vals = {}
		if calc_line.from_insulado:
			extra_vals = {
				'product_id':calc_line.product_ins_id.id,
				'mtf_template_id':calc_line.parent_id.template_id.id,
				}
		else:
			extra_vals = {'mtf_template_id':calc_line.template_id.id or False,}
		vals.update(extra_vals)
		return vals