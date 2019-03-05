# -*- coding: utf-8 -*-

from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime

class GlassRequisition(models.Model):
	_name = 'glass.requisition'
	_order_by='id desc'

	name = fields.Char('Orden de Requisición',default="/")
	table_number=fields.Char('Nro. de Mesa')
	date_order = fields.Date('Fecha Almacén',default=datetime.now())
	required_area = fields.Float('M2 Requeridos',compute="totals",digits=(20,4))
	required_mp = fields.Float('M2 Materia Prima',compute="totals",digits=(20,4))
	merma = fields.Float('Merma',compute="totals",digits=(20,4))
	state=fields.Selection([('draft','Borrador'),('confirm','Confirmada'),('process','Procesada'),('cancel','Cancelada')],'Estado',default='draft')
	picking_ids = fields.Many2many('stock.picking','glass_requisition_picking_rel','requisition_id','picking_id',u'Operaciones de Almacén')

	picking_mp_ids = fields.Many2many('stock.picking','glass_requisition_picking_mp_rel','requisition_id','picking_id',u'Operaciones de Almacén')
	picking_rt_ids = fields.Many2many('stock.picking','glass_requisition_picking_rt_rel','requisition_id','picking_id',u'Operaciones de Almacén')
	picking_drt_ids = fields.Many2many('stock.picking','glass_requisition_picking_drt_rel','requisition_id','picking_id',u'Operaciones de Almacén')
	picking_pt_ids = fields.Many2many('stock.picking','glass_requisition_picking_pt_rel','requisition_id','picking_id',u'Operaciones de Almacén')

	total_picking_mp = fields.Float('Total M2',compute="totals",digits=(20,4))
	total_picking_rt = fields.Float('Total M2',compute="totals",digits=(20,4))
	total_picking_drt = fields.Float('Total M2',compute="totals",digits=(20,4))


	production_order_ids = fields.Many2many('glass.order','glass_requisition_production_rel','requisition_id','order_id',u'Órdenes de Producción',compute="getprdorders")

	lot_ids = fields.One2many('glass.requisition.line.lot','requisition_id','Lotes')


	picking_type_mp = fields.Integer(u'Operación consumo materia prima ')
	picking_type_rt = fields.Integer(u'Operación consumo retazos')
	picking_type_drt = fields.Integer(u'Operación devolución retazos')
	picking_type_pr = fields.Integer(u'Operación producción')
	traslate_motive_mp = fields.Integer('Motivo traslado consumo materia prima ')
	traslate_motive_rt = fields.Integer('Motivo traslado consumo retazos')
	traslate_motive_drt = fields.Integer(u'Motivo traslado devolución retazos')
	traslate_motive_pr = fields.Integer(u'Motivo traslado  producción')

	product_id=fields.Many2one('product.product','Producto General')
	lot_id=fields.Many2one('glass.lot','Lote')	

	picking_count = fields.Integer(compute='_compute_glass_picking', string='Receptions', default=0)

	_sql_constraints = [
		('table_number_uniq', 'unique(table_number)', u'El número de mesa debe de ser único'),
	]

	@api.depends('picking_mp_ids','picking_rt_ids','picking_drt_ids')
	def _compute_glass_picking(self):
		pickings = self.mapped('picking_mp_ids')
		pickings_rt = self.mapped('picking_rt_ids')
		pickings_drt = self.mapped('picking_drt_ids')
		pickings = pickings + pickings_rt + pickings_drt
		self.picking_count = len(pickings)

	@api.multi
	def call_units(self):
		view = self.env.ref('glass_production_order.view_glass_make_uom_form')
		data = {
			'name': _('Agregar unidad'),
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'glass.make.uom',
			'view_id': view.id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		} 
		return data

	@api.multi
	def action_view_delivery_glass(self):
		
		action = self.env.ref('stock.action_picking_tree').read()[0]
		pickings = self.mapped('picking_mp_ids')
		pickings_rt = self.mapped('picking_rt_ids')
		pickings_drt = self.mapped('picking_drt_ids')
		pickings = pickings + pickings_rt + pickings_drt
		
		print("pickingjoin",','.join(map(str, pickings.ids)))
		print("picking",pickings)

		if len(pickings) > 1:
			action['domain'] = "[('id', 'in',[" + ','.join(map(str, pickings.ids)) + "])]"
			action['context'] = {
					'search_default_picking_type_id': '',
			}
		elif pickings:
			action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
			action['res_id'] = pickings.id
		return action

	@api.multi
	def create_glass_picking(self):
		return {
			'type':'ir.actions.act_window',
			'res_model': 'stock.picking',
			'view_mode':'form',
			'view_type':'form',
			'views': [(self.env.ref('stock.view_picking_form').id, 'form')],
			'context':{
				'origin':self.name,
				'default_fecha_kardex':self.date_order,
				'default_picking_type_id':self.picking_type_mp,
				'default_einvoice_12':self.traslate_motive_mp,
				'default_origin':self.name,
				'default_identifier':'mp',
				'identificador_glass':self.id,
				'default_identificador_glass':self.id
				}
		}

	@api.multi
	def create_glass_picking_rt(self):
		return {
			'type':'ir.actions.act_window',
			'res_model': 'stock.picking',
			'view_mode':'form',
			'view_type':'form',
			'views': [(self.env.ref('stock.view_picking_form').id, 'form')],
			'context':{
				'origin':self.name,
				'default_fecha_kardex':self.date_order,
				'default_picking_type_id':self.picking_type_rt,
				'default_einvoice_12':self.traslate_motive_rt,
				'default_origin':self.name,
				'default_identifier':'rt',
				'identificador_glass':self.id,
				'default_identificador_glass':self.id
				}
		}

	@api.multi
	def create_glass_picking_drt(self):
		return {
			'type':'ir.actions.act_window',
			'res_model': 'stock.picking',
			'view_mode':'form',
			'view_type':'form',
			'views': [(self.env.ref('stock.view_picking_form').id, 'form')],
			'context':{
				'origin':self.name,
				'default_fecha_kardex':self.date_order,
				'default_picking_type_id':self.picking_type_drt,
				'default_einvoice_12':self.traslate_motive_drt,
				'default_origin':self.name,
				'default_identifier':'drt',
				'identificador_glass':self.id,
				'default_identificador_glass':self.id
				}
		}

	@api.one
	def reopen(self):
		self.update({'state':'draft'})

	@api.one
	def confirm(self):
		config_data = self.env['glass.order.config'].search([])
		if len(config_data)==0:
			raise UserError(u'No se encontraron los valores de configuración de producción')		
		config_data = self.env['glass.order.config'].search([])[0]
		if self.name=='/':
			newname = config_data.seq_lot.next_by_id()
			self.update({'name':newname})
		self.update({'state':'confirm'})


	@api.model
	def default_get(self,fields):
		res = super(GlassRequisition,self).default_get(fields)
		config_data = self.env['glass.order.config'].search([])
		if len(config_data)==0:
			raise UserError(u'No se encontraron los valores de configuración de producción')		
		config_data = self.env['glass.order.config'].search([])[0]
		# newname = config_data.seq_requisi.next_by_id()
		res.update({'picking_type_mp':config_data.picking_type_mp.id})
		res.update({'picking_type_rt':config_data.picking_type_rt.id})
		res.update({'picking_type_drt':config_data.picking_type_drt.id})
		res.update({'picking_type_pr':config_data.picking_type_pr.id})
		res.update({'traslate_motive_mp':config_data.traslate_motive_mp.id})
		res.update({'traslate_motive_rt':config_data.traslate_motive_rt.id})
		res.update({'traslate_motive_drt':config_data.traslate_motive_drt.id})
		res.update({'traslate_motive_pr':config_data.traslate_motive_pr.id})
		# res.update({'name':newname})
		return res


	@api.multi
	def add_mp_picking(self):

		# search_view_ref = self.env.ref('account.view_account_invoice_filter', False)
		# form_view_ref = self.env.ref('stock.view_glass_pool_wizard_form', False)
		# tree_view_ref = self.env.ref('account.invoice_tree', False)
		# module = __name__.split('addons.')[1].split('.')[0]

		vals_default={
			'default_state':'draft',
		}
		view = self.env.ref('stock.view_picking_form')
		data = {
			'name': _('Agregar Materia Prima'),
			'context': self._context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'stock.picking',
			'view_id': view.id,
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context':vals_default,
		} 
		return data


	@api.model
	def create(self,vals):
		
		if 'table_number' in vals:
			if len(vals['table_number'])!=7:
				raise UserError(u'El número de mesa debe tener el formato M999999')		
			if vals['table_number'][0:1]!='M':
				raise UserError(u'El número de mesa debe tener el formato M999999')		
			if not vals['table_number'][1:].isnumeric():
				raise UserError(u'El número de mesa debe tener el formato M999999')
		if 'lot_ids' in vals:
			for lote in vals['lot_ids']:
				lote_act = self.env['glass.lot'].browse(lote[2]['lot_id'])
				lote[2]['m2']=lote_act.total_area
				lote[2]['user_id']=lote_act.create_uid.id
				lote[2]['crystal_count']=len(lote_act.line_ids)
		return super(GlassRequisition,self).create(vals)


	# Tener cuidado con esta vaina xq costo mucho hacer que funcione y aun asi
	# podria tener fallos:
	@api.one
	def write(self,vals):
		if 'lot_ids' in vals:
			for lote in vals['lot_ids']:
				if lote[2]:
					if 'lot_id' in lote[2]:
						lote_act = self.env['glass.lot'].browse(lote[2]['lot_id'])
						lote[2]['m2']=lote_act.total_area
						lote[2]['user_id']=lote_act.create_uid.id
						lote[2]['crystal_count']=len(lote_act.line_ids)
						for line in lote_act.line_ids:
							data = {
								'user_id':self.env.uid,
								'date':datetime.now(),
								'time':datetime.now().time(),
								'stage':'requisicion',
								'lot_line_id':line.id,
								'date_fisical':datetime.now(),
							}
							stage_obj = self.env['glass.stage.record']
							stage_obj.create(data)
							line.requisicion=True

		t = super(GlassRequisition,self).write(vals)
		if 'product_id' in vals:
			return t
		if 'table_number' in vals:
			if len(vals['table_number'])!=7:
				raise UserError(u'El número de mesa debe tener el formato M999999')		
			if vals['table_number'][0:1]!='M':
				raise UserError(u'El número de mesa debe tener el formato M999999')		
			if not vals['table_number'][1:].isnumeric():
				raise UserError(u'El número de mesa debe tener el formato M999999')
		# Verificamos los datos enviados relacionados a los productos:
		self.refresh()
		product = self._verify_data(self.lot_ids,self.picking_mp_ids,self.picking_rt_ids,self.picking_drt_ids)
		if product:
			self.product_id = product.id # Si todo sale bien seteamos el producto

		
		return t
		#return super(GlassRequisition,self).write(vals)

	# Verifica si todos los productos de los lotes de las glass.requisition.line.lot
	# son iguales y tbn verifica que el atributo (de a configuracion) coincida para 
	# los productos de los lotes de las glass.requisition.line.lot y los prods de los 
	# albaranes de materias primas etc.
	@api.multi
	def _verify_data(self,lot_lines,mp_lines,rt_lines,drt_ids):
		if len(lot_lines) == 0:
			return False
		try:
			config_attr = self.env['glass.order.config'].search([])[0].compare_attribute
		except IndexError as e:
			print('Error: ', e)
			raise UserError(u'No se ha encontrado los valores de configuración para el Atributo de comparación.')
		product = list(set(map(lambda x: x.lot_id.product_id , lot_lines))) # prod de los lot lines
		if len(product) > 1:
			raise UserError('Las lineas de lotes deben tener todas el mismo producto.')

		attribute = self.env['product.selecionable'].search([('atributo_id','=',config_attr.id),('product_id','=',product[0].product_tmpl_id.id)])

		if len(attribute) == 0:
			raise UserError('El atributo configurado: "'+str(config_attr.name)+'" no se ha encontrado en el producto de los lotes')
		attribute_value = attribute[0].valor_id.name
		if len(mp_lines) > 0:
			for picking in mp_lines:
				for move in picking.move_lines:
					attr = self.env['product.selecionable'].search([('atributo_id','=',config_attr.id),('product_id','=',move.product_id.product_tmpl_id.id)])
					if len(attr) == 0:
						raise UserError('El atributo configurado: "'+config_attr.name+'"  \n no se ha encontrado en el producto '+ move.product_id.name + ' de la orden de materias primas.')
					if attr[0].valor_id.name != attribute_value:
						raise UserError('El valor del atributo "'+config_attr.name+'"-'+str(attribute_value)+'\n no coincide con el del producto '+ move.product_id.name + ' de la orden de materias primas.')
		if len(rt_lines) > 0:
			for picking in rt_lines:
				for move in picking.move_lines:
					attr = self.env['product.selecionable'].search([('atributo_id','=',config_attr.id),('product_id','=',move.product_id.product_tmpl_id.id)])
					if len(attr) == 0:
						raise UserError('El atributo configurado: "'+config_attr.name+'"  \n no se ha encontrado en el producto '+ move.product_id.name + ' de la orden de materias primas.')
					if attr[0].valor_id.name != attribute_value:
						raise UserError('El valor del atributo "'+config_attr.name+'"-'+str(attribute_value)+'\n no coincide con el del producto '+ move.product_id.name + ' de la orden de materias primas-Retazos.')
		if len(drt_ids) > 0:
			for picking in drt_ids:
				for move in picking.move_lines:
					attr = self.env['product.selecionable'].search([('atributo_id','=',config_attr.id),('product_id','=',move.product_id.product_tmpl_id.id)])
					if len(attr) == 0:
						raise UserError('El atributo configurado: "'+config_attr.name+'"  \n no se ha encontrado en el producto '+ move.product_id.name + ' de la orden de materias primas.')
					if attr[0].valor_id.name != attribute_value:
						raise UserError('El valor del atributo "'+config_attr.name+'"-'+str(attribute_value)+'\n no coincide con el del producto '+ move.product_id.name + ' de la orden de Devoluciones-Retazos.')
		return product[0]
		

	@api.one
	def cancel(self):
		self.state='cancel'
		for line in self.picking_ids:
			line.action_cancel()
		return True 

	@api.onchange('lot_ids')
	def onchagelots(self):
		ops = []
		for line in self.lot_ids:
			for linelot in line.lot_id.line_ids:
				if linelot.order_prod_id.id not in ops:
					ops.append(linelot.order_prod_id.id)
		self.production_order_ids=ops


	@api.one
	def unlink(self):
		if self.state!='draft':
			raise UserError(u'No se puede borrar una Requisición que ha fue Procesada')		
		return super(GlassRequisition,self).unlink()

	@api.one
	def getprdorders(self):
		ops = []
		for line in self.lot_ids:
			for linelot in line.lot_id.line_ids:
				if linelot.order_prod_id.id not in ops:
					ops.append(linelot.order_prod_id.id)
		self.production_order_ids=ops



	@api.one
	def totals(self):
		n=0
		tpmp=0
		tprt=0
		tpdrt=0
		for l in self.lot_ids:
			n=n+l.lot_id.total_area

		m=0
		for l in self.picking_mp_ids:
			for d in l.move_lines:
				m=m+(d.product_uom_qty*d.product_uom.factor_inv)
				tpmp=tpmp+(d.product_uom_qty*d.product_uom.factor_inv)
		for l in self.picking_rt_ids:
			for d in l.move_lines:
				m=m+(d.product_uom_qty*d.product_uom.factor_inv)
				tprt=tprt+(d.product_uom_qty*d.product_uom.factor_inv)
				#print tprt,d.product_uom_qty
		j=0
		for l in self.picking_drt_ids:
			for d in l.move_lines:
				j=j+(d.product_uom_qty*d.product_uom.factor_inv)				
				tpdrt=tpdrt+(d.product_uom_qty*d.product_uom.factor_inv)

		self.required_area=n
		self.required_mp=m-j
		self.merma=(m-j)-n

		self.total_picking_mp=tpmp
		self.total_picking_rt=tprt
		self.total_picking_drt=tpdrt


	@api.model
	def _prepare_picking(self,pt,motive):
		useract = self.env.user
		return {
			'picking_type_id': pt.id,
			'partner_id': None,
			'date': datetime.now(),
			'origin': self.name,
			'location_dest_id': pt.default_location_dest_id.id,
			'location_id': pt.default_location_src_id.id,
			'company_id': useract.company_id.id,
			'einvoice12': motive.id,
		}



	@api.one
	def process(self):
		self.state='process'			
		n=0
		for l in self.lot_ids:
			n=n+l.lot_id.total_area
		totalsolicitado = n
		merma = self.merma

		for l in self.lot_ids:
			psol = (l.lot_id.total_area*100)/totalsolicitado
			mermaequi = merma*(psol/100)
			for sl in l.lot_id.line_ids:
				g = (sl.area*100)/l.lot_id.total_area
				mermaline = mermaequi*(g/100)
				sl.merma=mermaline






		# picking = self.env['stock.picking'].create(self._prepare_picking(pt_mp,motive))
		# apickings.append(picking.id)
		# useract = self.env.user
		# for l in self.mp_ids:
		# 	if not l.uom_id.is_retazo:
		# 		vals = {
		# 			'name': self.name or '',
		# 			'product_id': l.product_id.id,
		# 			'product_uom': l.uom_id.id,
		# 			'date': datetime.now(),
		# 			'date_expected': datetime.now(),
		# 			'location_id': pt_mp.default_location_src_id.id,
		# 			'location_dest_id': pt_mp.default_location_dest_id.id,
		# 			'picking_id': picking.id,
		# 			'partner_id': None,
		# 			'move_dest_id': False,
		# 			'state': 'draft',
		# 			'company_id': useract.company_id.id,
		# 			'picking_type_id': pt_mp.id,
		# 			'procurement_id': False,
		# 			'origin': self.name,
		# 			'route_ids': pt_mp.warehouse_id and [(6, 0, [x.id for x in pt_mp.warehouse_id.route_ids])] or [],
		# 			'warehouse_id': pt_mp.warehouse_id.id,
		# 			'product_uom_qty': l.qty,
		# 		}
		# 		self.env['stock.move'].create(vals)

		# pt_mp=config_data.picking_type_rt
		# motive = config_data.traslate_motive_rt
		# generar_retazo = False
		# for l in self.mp_ids:
		# 	if l.uom_id.is_retazo:
		# 		generar_retazo=True
		# 		break
		# if generar_retazo:
		# 	picking = self.env['stock.picking'].create(self._prepare_picking(pt_mp,motive))
		# 	apickings.append(picking.id)
		# 	for l in self.mp_ids:
		# 		if l.uom_id.is_retazo:
		# 			vals = {
		# 				'name': self.name or '',
		# 				'product_id': l.product_id.id,
		# 				'product_uom': l.uom_id.id,
		# 				'date': datetime.now(),
		# 				'date_expected': datetime.now(),
		# 				'location_id': pt_mp.default_location_src_id.id,
		# 				'location_dest_id': pt_mp.default_location_dest_id.id,
		# 				'picking_id': picking.id,
		# 				'partner_id': None,
		# 				'move_dest_id': False,
		# 				'state': 'draft',
		# 				'company_id': useract.company_id.id,
		# 				'picking_type_id': pt_mp.id,
		# 				'procurement_id': False,
		# 				'origin': self.name,
		# 				'route_ids': pt_mp.warehouse_id and [(6, 0, [x.id for x in pt_mp.warehouse_id.route_ids])] or [],
		# 				'warehouse_id': pt_mp.warehouse_id.id,
		# 				'product_uom_qty': l.qty,
		# 			}
		# 			self.env['stock.move'].create(vals)

		# pt_mp=config_data.picking_type_drt
		# motive = config_data.traslate_motive_drt
		# picking = self.env['stock.picking'].create(self._prepare_picking(pt_mp,motive))
		# apickings.append(picking.id)
		# for l in self.mp_ids:
		# 	if not l.uom_id.is_retazo:
		# 		vals = {
		# 			'name': self.name or '',
		# 			'product_id': l.product_id.id,
		# 			'product_uom': l.uom_id.id,
		# 			'date': datetime.now(),
		# 			'date_expected': datetime.now(),
		# 			'location_id': pt_mp.default_location_src_id.id,
		# 			'location_dest_id': pt_mp.default_location_dest_id.id,
		# 			'picking_id': picking.id,
		# 			'partner_id': None,
		# 			'move_dest_id': False,
		# 			'state': 'draft',
		# 			'company_id': useract.company_id.id,
		# 			'picking_type_id': pt_mp.id,
		# 			'procurement_id': False,
		# 			'origin': self.name,
		# 			'route_ids': pt_mp.warehouse_id and [(6, 0, [x.id for x in pt_mp.warehouse_id.route_ids])] or [],
		# 			'warehouse_id': pt_mp.warehouse_id.id,
		# 			'product_uom_qty': l.qty,
		# 		}
		# 		self.env['stock.move'].create(vals)	
		
		# self.picking_ids=apickings




class GlassRequisitionLineLot(models.Model):
	_name = 'glass.requisition.line.lot'

	lot_id = fields.Many2one('glass.lot','Lote')
	date=fields.Date('Fecha',default=datetime.now())
	user_id=fields.Many2one('res.users','Usuario')
	m2 = fields.Float('M2',digits=(20,4))
	requisition_id = fields.Many2one('glass.requisition','requisition')
	crystal_count=fields.Integer(u'Número de cristales')


	@api.onchange('lot_id')
	def onchangelot(self):
		### new
		self.m2 = self.lot_id.total_area
		self.date=self.lot_id.date
		self.user_id=self.lot_id.create_uid.id
		self.crystal_count=len(self.lot_id.line_ids)

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	identificador_glass = fields.Integer(index=True)
	identifier = fields.Char(index=True)

	@api.model
	def create(self,vals):
		record = super(StockPicking,self).create(vals)
		if record.identificador_glass > 0:		
			requisition = self.env['glass.requisition'].search([('id','=',record.identificador_glass)])
			aux = []
			if record.identifier == 'mp':
				for i in requisition.picking_mp_ids:
					aux.append(i[0].id)
				aux.append(record.id)
				requisition.picking_mp_ids = [(6,0,aux)]
			if record.identifier == 'rt':
				for i in requisition.picking_rt_ids:
					aux.append(i[0].id)
				aux.append(record.id)
				requisition.picking_rt_ids = [(6,0,aux)]
			if record.identifier == 'drt':
				for i in requisition.picking_drt_ids:
					aux.append(i[0].id)
				aux.append(record.id)
				requisition.picking_drt_ids = [(6,0,aux)]
		return record