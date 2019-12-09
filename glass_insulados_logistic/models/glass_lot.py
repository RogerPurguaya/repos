# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class GlassLotLine(models.Model):
	_inherit = 'glass.lot.line'

	#mtf_temp_process_line_id = fields.Many2one(related='order_line_id.mtf_temp_process_line_id')
	mtf_template_id = fields.Many2one(related='order_line_id.mtf_template_id',store=True)
	from_insulado = fields.Boolean(related='calc_line_id.from_insulado',store=True)

	def _get_requested_stages(self):
		res = super(GlassLotLine,self)._get_requested_stages()
		# add stages from template
		# FIXME: Match por el producto para obtener las etapas que le corresponden, no parece ser lo mejor pero funcionará...
		stages = []
		tmpl = self.mtf_template_id
		if self.from_insulado:
			line=tmpl.line_ids.filtered(lambda x: x.product_id==self.product_id and x.pos_ins_crystal)
			if line:
				line = line[0]
				stages = tmpl.ins_cr_1_stage_ids if line.pos_ins_crystal==1 else tmpl.ins_cr_2_stage_ids
				stages = stages.mapped('name')
		else:
			stages = tmpl.stage_ids.mapped('name')
		res.extend(stages)
		return res
