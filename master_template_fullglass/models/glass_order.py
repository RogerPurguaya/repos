# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class GlassOrderLine(models.Model):
	_inherit = 'glass.order.line'

	#mtf_temp_process_line_id = fields.Many2one('mtf.template.process.line',string=u'Línea de procesos')

	#mtf_template_id = fields.Many2one(compute='_get_master_template',string='Ficha Maestra',store=True)
	mtf_template_id = fields.Many2one('mtf.template',string='Ficha Maestra')

	# @api.depends('calc_line_id')
	# def _get_master_template(self):
	# 	for line in self:
	# 		calc = line.calc_line_id
	# 		line.mtf_template_id = calc.parent_id.template_id.id if calc.from_insulado else calc.template_id.id