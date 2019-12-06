# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class GlassOrder(models.Model):
	_inherit = 'glass.order'

	#mtf_req_line_ids = fields.One2many('mtf.requisition.material.line','glass_order_id')
	mtf_requirement_id = fields.Many2one('mtf.requisition',string=u'Requisición')
	mtf_req_line_ids = fields.Many2many('mtf.requisition.material.line',compute='_get_mtf_req_line_ids')
	mtf_have_reqs = fields.Boolean('Tiene Requerimientos',compute='_get_mtf_req_line_ids')

	@api.depends('line_ids')
	def _get_mtf_req_line_ids(self):
		calc_lines = self.env['glass.sale.calculator.line']
		for rec in self:
			for line in rec.line_ids:
				if line.calc_line_id.from_insulado:
					calc_lines |= line.calc_line_id.parent_id
				else:
					calc_lines |= line.calc_line_id
			# TODO: solo costeados (excluyendo los q son cristales)
			req_lines = calc_lines.mapped('material_line_ids')
			rec.mtf_req_line_ids = req_lines.filtered(lambda x: not x.not_cost and not x.to_produce)
			rec.mtf_have_reqs = bool(rec.mtf_req_line_ids)

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