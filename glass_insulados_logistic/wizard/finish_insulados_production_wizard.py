# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class IlFinishInsuladosWizard(models.TransientModel):
	_name = 'il.finish.insulados.wizard'

	_description = u'Culminación de proceso para insulados'

	glass_order_ids = fields.Many2many('glass.order',string=u'Órdenes de producción')
	picking_type_id = fields.Many2one('stock.picking.type',string='Tipo de Operación')
	req_traslate_motive = fields.Many2one('einvoice.catalog.12',u'Motivo de traslado')
	line_ids = fields.One2many('il.finish.insulados.wizard.line','wizard_id')

	def get_new_element(self):
		default_pick_type = self.env['glass.order.config'].search([],limit=1).pick_type_in_ins_id
		if not default_pick_type:
			raise UserError(u'No se ha encontrado el tipo de picking por defecto para ésta operación en sus parámetros de configuración.')
		wizard = self.create({'picking_type_id':default_pick_type.id})
		return {
			'name':u'Traslado de Insulados',
			'res_id': wizard.id,
			'type': 'ir.actions.act_window',
			'res_model': wizard._name,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}

	def get_ins_crystals(self):
		"""Obtener solo órdenes con requirimiento completo"""
		self.ensure_one()
		glass_order_ids=self.glass_order_ids.filtered(lambda o: 'ended' in o.mtf_requirement_ids.mapped('state'))
		if not glass_order_ids:
			raise UserError(u"Ninguna de las Op's seleccionadas ha finalizado su Orden de requisición de Ficha maestra")
		#lines = self.glass_order_ids.mapped('line_ids.lot_line_id').filtered(lambda l: l.from_insulado and l.templado and not l.is_break)
		self.line_ids.unlink()
		## get complete process:
		# solo cristales cuyo albarán de ingreso esté realizado:
		sql = """
			SELECT 
			gll.id
			FROM 
			glass_order_line_stock_move_rel glsm_rel
			join glass_order_line gol on gol.id = glsm_rel.glass_order_line_id
			join stock_move sm on sm.id = glsm_rel.stock_move_id
			join glass_lot_line gll on gll.order_line_id = gol.id
			WHERE 
			sm.state = 'done'
			and gll.from_insulado
			and (gll.insulado = false or gll.insulado is null)
			and gll.templado = true
			and (gll.producido = false or gll.producido is null)
			and gll.il_in_transfer = true
		"""
		self._cr.execute(sql)
		res = self._cr.fetchall()
		if not any(res): 
			return {"type": "ir.actions.do_nothing",}
		res = [r[0] for r in res]
		available_items = []
		# only with mtf_requirement_ids ended..
		for order in glass_order_ids:
			calcs = order.line_ids.mapped('calc_line_id.parent_id')
			#ext_domain = [('insulado','=',False),('templado','=',True),('producido','=',False),('il_in_transfer','=',True),('id','in',res)]
			ext_domain = [('id','in',res)]
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
		return {"type": "ir.actions.do_nothing",}


	def process_transfer(self):
		lines = self.line_ids
		if not lines:
			raise UserError('No hay cristales insulados disponibles para ingresar a Producto Terminado')
		#lines = self.line_ids.mapped('lot_line_id')
		products = lines.mapped('product_id')
		pick_vals = self._prepare_pick_vals()
		pick = self.env['stock.picking'].create(pick_vals)
		move_vals = []
		for product in products:
			filt = lines.filtered(lambda l: l.product_id==product)
			quantity = sum(filt.mapped('area'))
			glass_ids = filt.mapped('base_crystals.order_line_id').ids
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
		
		# FIXME Debebería registrarse las etapas si no se consigue transferir el albarán? si el tipo de 
		# de picking es de producción no habría problemas al transferir, pero si no uhmm XDXD
		lines.write({'insulado':True})
		lot_lines = lines.mapped('base_crystals')
		lot_lines.register_stage('insulado')
		lot_lines.with_context(force_register=True).register_stage('producido')
		lot_lines.with_context(force_register=True).register_stage('ingresado')
		lot_lines.mapped('order_line_id').write({'state':'instock'})
		action = self.env.ref('stock.action_picking_tree_all').read()[0]
		action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
		action['res_id'] = pick.id
		return action

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

	
		
class IlFinishInsuladosWizardLine(models.TransientModel):
	_name = 'il.finish.insulados.wizard.line'

	wizard_id = fields.Many2one('il.finish.insulados.wizard',string=u'Wizard')
	calc_line_id = fields.Many2one('glass.sale.calculator.line',string=u'Línea de Cristal')
	crystal_num = fields.Char('Nro de Cristal')
	product_id = fields.Many2one(related='calc_line_id.calculator_id.product_id',string="Producto")
	uom_id = fields.Many2one(related='product_id.uom_id',string="Unidad")
	quantity = fields.Integer(default=1,string='Cantidad')
	base1 = fields.Integer(related='calc_line_id.base1')
	base2 = fields.Integer(related='calc_line_id.base2')
	height1 = fields.Integer(related='calc_line_id.height1')
	height2 = fields.Integer(related='calc_line_id.height2')
	area = fields.Float(related='calc_line_id.area')
	base_crystals = fields.Many2many('glass.lot.line',string=u'Cristales producidos que lo conforman')

	def view_crystals(self):
		return {
			'name':'Cristales Componentes',
			'type': 'ir.actions.act_window',
			'res_model': 'glass.lot.line',
			'view_id': self.env.ref('glass_production_order.glass_lot_line_view_tree').id,
			'view_mode': 'tree',
			'view_type': 'form',
			'target': 'new',
			'domain':[('id','in',self.base_crystals.ids)]
			}
		
		

