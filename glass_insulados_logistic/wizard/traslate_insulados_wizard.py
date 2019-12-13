# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class IlTraslateInsuladosWizard(models.TransientModel):
	_name = 'il.traslate.insulados.wizard'

	_description = u'Traslado de crsitales para insulado a planta de prod. de insulados.'

	picking_type_id = fields.Many2one('stock.picking.type',string='Tipo de Operación')
	req_traslate_motive = fields.Many2one('einvoice.catalog.12',u'Motivo de traslado')
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
		if not self.line_ids:
			raise UserError('No hay cristales para insulado disponibles para enviar.')
		lines = self.line_ids.mapped('lot_line_id')
		products = lines.mapped('product_id')
		pick_vals = self._prepare_pick_vals()
		pick = self.env['stock.picking'].create(pick_vals)
		move_vals = []
		for product in products:
			filt = lines.filtered(lambda l: l.product_id==product)
			quantity = sum(filt.mapped('area'))
			glass_ids = filt.mapped('order_line_id').ids
			move_vals.append((0,0,self._prepare_move_vals(product,quantity,glass_ids)))
		pick.write({'move_lines':move_vals})
		pick.action_confirm()
		pick.action_assign()

		if pick.state == 'assigned':
			action = pick.do_new_transfer()
			if type(action) is dict and action['res_model'] == 'stock.immediate.transfer':
				context = action['context']
				sit = self.env['stock.immediate.transfer'].with_context(context).create({'pick_id':pick.id})	
				sit.process()
				
		lines.write({'il_in_transfer':True})
		action = self.env.ref('stock.action_picking_tree_all').read()[0]
		action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
		action['res_id'] = pick.id
		return action

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
		and (gll.il_in_transfer = false or gll.il_in_transfer is null)
		and (gll.insulado = false or gll.insulado is null)
		"""
		self._cr.execute(query)
		results = self._cr.fetchall()
		res.update({
			'picking_type_id':default_pick_type.id,
			'line_ids':[(0,0,{'lot_line_id':r[0]}) for r in results],})
		return res

	def _prepare_pick_vals(self):
		current_date = fields.Date.context_today(self)
		pick_type = self.picking_type_id
		return {
			# TODO que partner le ponemos??
			# al parecer siempres serán transf. internas, si son incoming, asignar un partner 
			'partner_id':False,
			'picking_type_id':pick_type.id,
			'date':current_date,
			'fecha_kardex':current_date,
			'location_dest_id':pick_type.default_location_dest_id.id,
			'location_id': pick_type.default_location_src_id.id,
			'company_id': self.env.user.company_id.id,
			'einvoice_12': self.req_traslate_motive.id,
		}

	def _prepare_move_vals(self,product,qty,glass_ids):
		current_date = fields.Date.context_today(self)
		pick_type = self.picking_type_id
		return {
		'name': product.name,
		'product_id': product.id,
		'product_uom': product.uom_id.id,
		'date':current_date,
		'date_expected':current_date,
		'picking_type_id': pick_type.id,
		'location_id': pick_type.default_location_src_id.id,
		'location_dest_id': pick_type.default_location_dest_id.id,
		'partner_id': False,
		'move_dest_id': False,
		'state': 'draft',
		'company_id':self.env.user.company_id.id,
		'procurement_id': False,	
		'route_ids':pick_type.warehouse_id and [(6,0,pick_type.warehouse_id.route_ids.ids)] or [],
		'warehouse_id': pick_type.warehouse_id and pick_type.warehouse_id.id or False,
		'product_uom_qty':qty,
		'glass_order_line_ids':[(6,0,glass_ids or [])]
		}
		
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
		

