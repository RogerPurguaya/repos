# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class IlTraslateInsuladosWizard(models.TransientModel):
	_name = 'il.traslate.insulados.wizard'

	_description = u'Traslado de crsitales para insulado a planta de prod. de insulados.'

	picking_type_id = fields.Many2one('stock.picking.type',string='Tipo de Operación')
	line_ids = fields.One2many('il.traslate.insulados.wizard.line','wizard_id')
	
	
	def get_new_element(self):
		wizard = self.create({})
		return {
			'name':u'Traslado de Insulados',
			'res_id': wizard.id,
			'type': 'ir.actions.act_window',
			'res_model': wizard._name,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}


	def process_transfer(self):
		"""Obtener solo órdenes con requirimiento completo"""
		return {"type": "ir.actions.do_nothing",} 
		# self.ensure_one()
		# glass_order_ids=self.glass_order_ids.filtered(lambda o: 'ended' in o.mtf_requirement_ids.mapped('state'))
		# if not glass_order_ids:
		# 	raise UserError(u"Ninguna de las Op's seleccionadas ha finalizado su Orden de requisición de Ficha maestra")
		# #lines = self.glass_order_ids.mapped('line_ids.lot_line_id').filtered(lambda l: l.from_insulado and l.templado and not l.is_break)
		# self.line_ids.unlink()
		# ## get complete process:
		# available_items = []
		# # only with mtf_requirement_ids ended..
		# for order in glass_order_ids:
		# 	calcs = order.line_ids.mapped('calc_line_id.parent_id')
		# 	ext_domain = [('insulado','=',False),('templado','=',True),('producido','=',False)]
		# 	completes_dict = calcs._get_insulados_dict_crystals(ext_domain,only_completes=True)
		# 	for k,v in completes_dict.items():
		# 		calc = calcs.filtered(lambda l: l.id == k)
		# 		for k2,v2 in v.items():
		# 			available_items.append((0,0,{
		# 			'calc_line_id':calc.id,
		# 			'crystal_num':k2,
		# 			'base_crystals':[(6,0,v2)]
		# 			}))
		# self.write({'line_ids':available_items})
		# return {"type": "ir.actions.do_nothing",}

	@api.model
	def default_get(self,default_fields):
		res = super(IlTraslateInsuladosWizard,self).default_get(default_fields)
		default_pick_type = self.env['glass.order.config'].search([],limit=1).pick_type_out_ins_id
		if not default_pick_type:
			raise UserError(u'No se ha encontrado el tipo de picking por defecto para ésta operación en sus parámetros de configuración.')
		## get aptos para ir a lima insulados:
		query = """
		select 
		id 
		from glass_lot_line gll
		where gll.from_insulado = true
		and gll.templado = true 
		and is_break = false
		and active = true
		and (gll.insulado = false or gll.insulado is null)
		"""
		self._cr.execute(query)
		results = self._cr.fetchall()
		res.update({
			'picking_type_id':default_pick_type.id,
			'line_ids':[(0,0,{'lot_line_id':r[0]}) for r in results],})
		return res


	def _prepare_pick_vals(self):
		return {

		}

	def _prepare_move_vals(self):
		pass
		
class IlTraslateInsuladosWizardLine(models.TransientModel):
	_name = 'il.traslate.insulados.wizard.line'

	wizard_id = fields.Many2one('il.traslate.insulados.wizard',string=u'Wizard')
	selected = fields.Boolean('Seleccionado',default=True)
	lot_line_id = fields.Many2one('glass.lot.line',string=u'Línea de Cristal')
	order_id = fields.Many2one(related='lot_line_id.order_prod_id')
	partner_id = fields.Many2one(related='order_id.partner_id')
	crystal_number = fields.Char(related='lot_line_id.nro_cristal')
	
	product_id = fields.Many2one(related='lot_line_id.product_id',string="Producto")
	uom_id = fields.Many2one(related='product_id.uom_id',string="Unidad")
	base1 = fields.Integer(related='lot_line_id.base1')
	base2 = fields.Integer(related='lot_line_id.base2')
	height1 = fields.Integer(related='lot_line_id.altura1')
	height2 = fields.Integer(related='lot_line_id.altura2')
	from_insulado = fields.Boolean('Para insulado',related='lot_line_id.from_insulado')
		

