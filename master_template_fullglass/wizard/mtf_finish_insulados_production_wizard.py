# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class MtfFinishInsuladosWizard(models.TransientModel):
	_name = 'mtf.finish.insulados.wizard'

	_description = u'Culminación de proceso para insulados'

	glass_order_ids = fields.Many2many('glass.order',string=u'Órdenes de producción')

	line_ids = fields.One2many('mtf.finish.insulados.wizard.line')

	def get_ins_crystals(self):
		"""Obtener solo órdenes con requirimiento completo"""
		self.ensure_one()
		glass_order_ids=self.glass_order_ids.filtered(lambda o: 'ended' in o.mtf_requirement_ids.mapped('state'))
		if not glass_order_ids:
			raise UserError(u"Ninguna de las ops seleccionadas ha finalizado su Orden de requisición de Ficha maestra")
		#lines = self.glass_order_ids.mapped('line_ids.lot_line_id').filtered(lambda l: l.from_insulado and l.templado and not l.is_break)
		self.line_ids.unlink()
		## get complete process:
		available_items = []
		# only with mtf_requirement_ids ended..
		for order in glass_order_ids:
			calcs = order.line_ids.mapped('calc_line_id.parent_id')
			ext_domain = [('insulado','=',False),('templado','=',True),('producido','=',False)]
			completes_dict = calcs._get_insulados_dict_crystals(ext_domain,only_completes=True)
			for k,v in completes_dict.items():
				calc = calcs.filtered(lambda l: l.id == k)
				for k2,v2 in v.items():
					available_items.append((0,0,{
					'calc_line_id':calc.id,
					'crystal_num':k2,
					'base_crystals':[(6,0,v2)]
					}))
		self.write({'line_ids':available_items})
		
class MtfFinishInsuladosWizardLine(models.TransientModel):
	_name = 'mtf.finish.insulados.wizard.line'

	wizard_id = fields.Many2one('mtf.finish.insulados.wizard',string=u'Wizard')
	calc_line_id = fields.Many2one('glass.sale.calculator.line',string=u'Línea de Cristal')
	crystal_num = fields.Char('Nro de Crsital')
	product_id = fields.Many2one(related='calc_line_id.product_id')
	uom_id = fields.Many2one(related='product_id.uom_id')
	quantity = fields.Integer(default=1)
	base1 = fields.Integer(related='calc_line_id.base1')
	base2 = fields.Integer(related='calc_line_id.base2')
	height1 = fields.Integer(related='calc_line_id.height1')
	height2 = fields.Integer(related='calc_line_id.height2')
	base_crystals = fields.Many2many('glass.lot.line',u'Cristales producidos que lo conforman')

