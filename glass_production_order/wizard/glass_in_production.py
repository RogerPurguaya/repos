# -*- coding: utf-8 -*-

from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta
from functools import reduce

class GlassInProductionWizard(models.TransientModel):
	_name='glass.in.production.wizard'
	
	stock_type_id = fields.Many2one('stock.picking.type',u'Operación de almacén') 
	date_in = fields.Date('Fecha ingreso',default=(datetime.now()-timedelta(hours=5)).date())
	start_date = fields.Date(default=datetime.now().date())
	end_date = fields.Date(default=datetime.now().date())
	order_ids = fields.One2many('glass.in.order','mainid','order_id')
	line_ids = fields.Many2many('glass.order.line','glass_in_lineorder_rel','in_id','line_id',string="Lineas")
	order_id = fields.Many2one('glass.order','Filtrar OP')
	search_param = fields.Selection([('glass_order','Orden de Produccion'),('search_code','Lectura de barras')],string='Busqueda por',default='search_code')
	message_erro = fields.Char()
	location_id  = fields.Many2one('custom.glass.location',string='Ubicacion')
	search_code  = fields.Char(string='Codigo de busqueda')

	@api.multi
	def get_new_element(self):
		wizard = self.env['glass.in.production.wizard'].create({})
		return {
			'res_id':wizard.id,
			'name':'Ingreso a la Produccion',
			'type': 'ir.actions.act_window',
			'res_model': 'glass.in.production.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}

	@api.multi
	def get_all_available(self):
		self.ensure_one()
		#start = datetime.strptime(self.start_date)
		if not self.start_date or not self.end_date:
			raise UserError('No ha colocado fechas de Inicio y/o fin.')
		start = datetime.strptime(self.start_date,"%Y-%m-%d").date()-timedelta(hours=5)
		end = datetime.strptime(self.end_date,"%Y-%m-%d").date()-timedelta(hours=5)
		stages = self.env['glass.stage.record'].search([('date','<=',end),('date','>=',start),('stage','=','templado')])
		lines = stages.mapped('lot_line_id').mapped('order_line_id').filtered(lambda x:x.state == 'ended')
		for item in lines:
			if item.id not in self.line_ids.ids:
				item.location_tmp = self.location_id.id
				self.write({'line_ids':[(4,item.id)]})
		return {"type": "ir.actions.do_nothing",}


	@api.multi
	def refresh_selected_lines(self):
		will_removed = self.line_ids.filtered(lambda x: x.order_id.id not in self.order_ids.mapped('order_id').ids)
		for item in will_removed.ids:
			self.write({'line_ids':[(3,item)]})
		return {"type": "ir.actions.do_nothing",}

	@api.depends('line_ids')
	@api.onchange('search_code')
	def onchangecode(self):
		config = self.env['glass.order.config'].search([])
		if len(config)==0:
			raise UserError(u'No se encontraron los valores de configuración de producción')		
		config = self.env['glass.order.config'].search([])[0]
		if self.search_code:			
			existe = self.env['glass.lot.line'].search([('search_code','=',self.search_code)])
			if len(existe)==1:
				line = existe.order_line_id
				if line.state!='ended':
					self.message_erro = 'La linea de orden no se encuentra en estado finalizado'
					self.search_code=""
					return
				this_obj=self.env['glass.in.production.wizard'].browse(self._origin.id) 
				if line not in this_obj.line_ids:
					line.location_tmp = self.location_id.id
					this_obj.write({'line_ids':[(4,line.id)]})
					self.search_code=""
					return {'value':{'line_ids':this_obj.line_ids.ids,'order_ids':this_obj.order_ids.ids}}
				else:
					self.message_erro = 'El registro ya se encuentra en la lista'
					self.search_code=""
			else:
				self.message_erro="Registro no encontrado!"
				self.search_code=""
				return
		else:
			return
	
	@api.onchange('order_id')
	def onchange_order_id(self):
		vals = {}
		aorder=[]
		for existente in self.order_ids:
			vals={
				'selected':existente.selected,
				'order_id':existente.order_id.id,
				'partner_id':existente.partner_id.id,
				'date_production':existente.date_production,
				'total_pzs':existente.total_pzs,
				'total_area':existente.total_area,
				}
			aorder.append((0,0,vals))
		if self.order_id:
			vals={
				'selected':True,
				'order_id':self.order_id.id,
				'partner_id':self.order_id.partner_id.id,
				'date_production':self.order_id.date_production,
				'total_pzs':self.order_id.total_pzs,
				'total_area':self.order_id.total_area,
				}
			aorder.append((0,0,vals))
		return {'value':{'order_ids':aorder}}

	@api.depends('line_ids')
	@api.onchange('order_ids')
	def getlines(self):	
		lines = self.order_ids.filtered(lambda x:x.selected).mapped('order_id').mapped('line_ids').filtered(lambda x:x.state=='ended')
		if len(lines)>0:
			this_obj = self.env['glass.in.production.wizard'].browse(self._origin.id)
			for item in lines:
				if item not in this_obj.line_ids:
					item.location_tmp = self.location_id.id
					this_obj.write({'line_ids':[(4,item.id)]})
			return {'value':{'line_ids':this_obj.line_ids.ids}}

	@api.model
	def default_get(self,fields):
		res = super(GlassInProductionWizard,self).default_get(fields)
		config = self.env['glass.order.config'].search([])
		if len(config)==0:
			raise UserError(u'No se encontraron los valores de configuración de producción')		
		config = self.env['glass.order.config'].search([])[0]
		res.update({'stock_type_id':config.picking_type_pt.id})
		return res

	@api.multi
	def makeingreso(self):
		try:
			config = self.env['glass.order.config'].search([])[0]
		except IndexError:
			raise UserError(u'No se encontraron los valores de configuración de producción')
		self.verify_constrains(self.date_in)
		picking = self.env['stock.picking'].create({
			'picking_type_id': self.stock_type_id.id,
			'partner_id': None,
			'date': (datetime.now()-timedelta(hours=5)).date(),
			'fecha_kardex': self.date_in,
			#'origin': order.name,
			'apt_in':True,
			'location_dest_id': self.stock_type_id.default_location_dest_id.id,
			'location_id': self.stock_type_id.default_location_src_id.id,
			'company_id': self.env.user.company_id.id,
			'einvoice_12': config.traslate_motive_pt.id,
		})
		for prod in self.line_ids.mapped('product_id'):
			lines = self.line_ids.filtered(lambda x: x.product_id.id == prod.id)
			total_area = sum(lines.mapped('area'))
			self.env['stock.move'].create({
				'name': prod.name or '',
				'product_id': prod.id,
				'product_uom': prod.uom_id.id,
				'date': (datetime.now()-timedelta(hours=5)).date(),
				'date_expected': (datetime.now()-timedelta(hours=5)).date(),
				'location_id': self.stock_type_id.default_location_src_id.id,
				'location_dest_id': self.stock_type_id.default_location_dest_id.id,
				'picking_id': picking.id,
				'partner_id': None,
				'move_dest_id': False,
				'state': 'draft',
				'company_id': self.env.user.company_id.id,
				'picking_type_id': self.stock_type_id.id,
				'procurement_id': False,
				#'origin': order.name,
				'route_ids': self.stock_type_id.warehouse_id and [(6, 0, [x.id for x in self.stock_type_id.warehouse_id.route_ids])] or [],
				'warehouse_id': self.stock_type_id.warehouse_id.id,
				'product_uom_qty': total_area,
				'glass_order_line_ids': [(6,0,lines.ids)]
			})
		context = None
		action = picking.do_new_transfer()
		if type(action) == type({}):
			if action['res_model'] == 'stock.immediate.transfer' or action['res_model'] == 'stock.backorder.confirmation':
				context = action['context']
				sit = self.env['stock.immediate.transfer'].with_context(context).create({'pick_id':picking.id})	
				sit.process()
			elif action['res_model'] == 'confirm.date.picking':
				context = action['context']
				cdp = self.env['confirm.date.picking'].with_context(context).create({'pick_id':picking.id,'date':picking.fecha_kardex})
				res = cdp.changed_date_pincking()
			
		for line in self.line_ids:
			if line.location_tmp:
				line.write({'locations': [(4,line.location_tmp.id)]})
			line.write({
				'state' : 'instock',
				'location_tmp':False,
				})
			line.lot_line_id.ingresado = True
			self.env['glass.stage.record'].create({
				'user_id':self.env.uid,
				'date':(datetime.now()-timedelta(hours=5)).date(),
				'time':(datetime.now()-timedelta(hours=5)).time(),
				'stage':'ingresado',
				'lot_line_id':line.lot_line_id.id,
			})
		for order in self.line_ids.mapped('order_id'):
			pendings = order.line_ids.filtered(lambda x: x.state in ('process','ended'))	
			if not any(pendings):
				order.state='ended'
		return {
				'name':picking.name,
				'res_id':picking.id,
				'view_type':'form',
				'view_mode':'form',
				'res_model':'stock.picking',
				'type':'ir.actions.act_window',
				}

	@api.multi
	def verify_constrains(self,date):
		# validando restricciones de terminos de pago (desactivado temporalmente NO BORRAR):
		# with_pay_terms = self.line_ids.filtered(lambda x: x.order_id.sale_order_id.payment_term_id)
		# if len(with_pay_terms) > 0:
		# 	conf=self.env['config.payment.term'].search([('operation','=','enter_apt')])
		# 	if len(conf) == 1: # solo puede estar en una conf
		# 		msg =''
		# 		for item in with_pay_terms:
		# 			sale = item.order_id.sale_order_id
		# 			if sale.payment_term_id.id in conf[0].payment_term_ids.ids:
		# 				invoice = sale.invoice_ids[0]
		# 				payed = invoice.amount_total - invoice.residual
		# 				percentage = (payed/invoice.amount_total) * 100
		# 				if percentage < conf[0].minimal:
		# 					msg += '-> '+item.crystal_number+' '+item.product_id.name+'\n'
		# 					raise exceptions.Warning('Las facturas de los siguientes cristales no fueron pagadas al '+str(conf[0].minimal)+' %.:\n'+msg)
		# 	else:
		# 		raise UserError('No ha configurado las condiciones para el Plazo de pago al Ingresar a APT')

		# currency_obj = self.env['res.currency'].search([('name','=','USD')])
		# if len(currency_obj)>0:
		# 	currency_obj = currency_obj[0]
		# else:
		# 	raise UserError( 'Error!\nNo existe la moneda USD \nEs necesario crear la moneda USD para un correcto proceso.' )

		# tipo_cambio = self.env['res.currency.rate'].search([('name','=',str(date)),('currency_id','=',currency_obj.id)])

		# if len(tipo_cambio)>0:
		# 	tipo_cambio = tipo_cambio[0]
		# else:
		# 	raise UserError( u'Error!\nNo existe el tipo de cambio para la fecha: '+ str(date) + u'\n Debe actualizar sus tipos de cambio para realizar esta operación')

		bad_lines = self.line_ids.mapped('lot_line_id').filtered(lambda x: not x.requisicion)
		if len(bad_lines) > 0:
			msg = ''
			for item in bad_lines:
				msg += u'-> Lote: %s -> Cristal Nro: %s\n.'%(item.lot_id.name,item.nro_cristal)
			raise UserError(u'Los siguientes Cristales no tienen order de Requisicion:\n'+msg+'Recuerde: Los lotes de los cristales a ingresar deben tener Orden de requisicion')


class GlassInOrder(models.TransientModel):
	_name = "glass.in.order"

	selected = fields.Boolean('Seleccionada')
	order_id = fields.Many2one('glass.order','Orden')
	partner_id = fields.Many2one('res.partner','Cliente')
	date_production = fields.Date(u'Fecha de Producción')
	total_pzs = fields.Float("Cantidad")
	total_area = fields.Float(u'M2')
	
	mainid=fields.Many2one('glass.in.production.wizard','mainid')
