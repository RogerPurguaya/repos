# -*- coding: utf-8 -*-
from odoo import fields, models,api,exceptions, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta

class GlassRequisition(models.Model):
	_name = 'glass.requisition'
	_order_by='id desc'

	name = fields.Char('Orden de Requisicion',default="/")
	table_number=fields.Char('Nro. de Mesa')
	date_order = fields.Date('Fecha Almacen',default=(datetime.now()-timedelta(hours=5)).date())
	required_area = fields.Float('M2 Requeridos',compute="totals",digits=(20,4))
	required_mp   = fields.Float('M2 Materia Prima',compute="totals",digits=(20,4))
	returned_area = fields.Float('M2 Devueltos',compute="totals",digits=(20,4))
	used_area     = fields.Float('M2 Usados',compute="totals",digits=(20,4))
	merma = fields.Float('Merma',compute="totals",digits=(20,4))
	state = fields.Selection([('draft','Borrador'),('confirm','Confirmada'),('process','Procesada'),('cancel','Cancelada')],'Estado',default='draft')
	picking_ids = fields.Many2many('stock.picking','glass_requisition_picking_rel','requisition_id','picking_id',u'Operaciones de Almacen',compute='_get_picking_ids')
	picking_mp_ids = fields.Many2many('stock.picking','glass_requisition_picking_mp_rel','requisition_id','picking_id',u'Operaciones de Almacen')
	picking_rt_ids = fields.Many2many('stock.picking','glass_requisition_picking_rt_rel','requisition_id','picking_id',u'Operaciones de Almacen')
	picking_drt_ids = fields.Many2many('stock.picking','glass_requisition_picking_drt_rel','requisition_id','picking_id',u'Operaciones de Almacen')
	total_picking_mp  = fields.Float('Total M2',compute="totals",digits=(20,4))
	total_picking_rt  = fields.Float('Total M2',compute="totals",digits=(20,4))
	total_picking_drt = fields.Float('Total M2',compute="totals",digits=(20,4))
	production_order_ids = fields.Many2many('glass.order','glass_requisition_production_rel','requisition_id','order_id',u'ordenes de Produccion',compute="getprdorders")
	lot_ids    = fields.One2many('glass.requisition.line.lot','requisition_id','Lotes')
	product_id = fields.Many2one('product.product','Producto General')
	picking_count = fields.Integer(compute='_compute_glass_picking', string='Receptions', default=0)
	raw_materials = fields.One2many('requisition.worker.material','requisition_id',string='Materias Primas')
	scraps = fields.One2many('requisition.worker.scraps','requisition_id',string='Retazos')
	return_scraps = fields.One2many('requisition.worker.scraps.return','requisition_id',string='Devolucion de Retazos')
	_sql_constraints = [('table_number_uniq', 'unique(table_number)', u'El numero de mesa debe de ser unico'),]

	@api.depends('picking_mp_ids','picking_rt_ids','picking_drt_ids')
	def _get_picking_ids(self):
		for rec in self:
			pickings      = rec.mapped('picking_mp_ids')
			pickings_rt   = rec.mapped('picking_rt_ids')
			pickings_drt  = rec.mapped('picking_drt_ids')
			rec.picking_ids = pickings + pickings_rt + pickings_drt
	
	@api.depends('picking_ids')
	def _compute_glass_picking(self):
		for rec in self:
			rec.picking_count = len(rec.picking_ids)

	@api.multi
	@api.depends('table_number','name')
	def name_get(self):
		result = []
		for req in self:
			name = req.table_number + ' - ' + req.name
			result.append((req.id, name))
		return result

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|',('table_number', operator, name), ('name',operator,name)]
		requisitions = self.search(domain + args, limit=limit)
		return requisitions.name_get()

	# boton de pickings
	@api.multi
	def action_view_delivery_glass(self):
		action = self.env.ref('stock.action_picking_tree').read()[0]
		if len(self.picking_ids) > 1:
			action['domain']="[('id','in',["+','.join(map(str,self.picking_ids.ids)) + "])]"
			action['context'] = {'search_default_picking_type_id': '',}
		elif len(self.picking_ids) == 1:
			action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
			action['res_id'] = self.picking_ids[0].id
		return action

	@api.multi
	def get_allowed_materials(self,product_id):
		config = self.env['glass.order.config'].search([])
		if len(config) == 0:
			raise exceptions.Warning('No ha encontrado la configuracion de produccion.')
		allowed = config[0].requisition_materials_ids.filtered(lambda x: x.product_id.id == product_id.id)
		if len(allowed) == 0:
			raise exceptions.Warning('No se ha encontrado la lista de materiales para: '+self.product_id.name + ' en este tipo de requisicion.\nConfigure su lista de materiales en: Produccion->Parametros->Orden de Requisicion->Materiales de Requisicion.')
		elif len(allowed.materials_ids) == 0:
			raise exceptions.Warning('La lista de materiales permitidos para '+self.product_id.name + ' en este tipo de operacion esta vacia')
		else:
			return allowed.materials_ids

	@api.multi
	def end_selected(self):
		objs = self._context.get('active_ids')
		objs = self.browse(objs).filtered(lambda x: x.state == 'confirm')
		if not objs:
			raise exceptions.Warning('Solo es posible Finalizar Requisiciones en estado confirmado')
		for item in objs:
			item.process()
			
	@api.one
	def confirm(self):
		conf = self.env['glass.order.config'].search([])
		if len(conf)==0:
			raise UserError(u'No se encontraron los valores de configuracion de produccion')		
		conf = self.env['glass.order.config'].search([])[0]
		if conf.seq_requisi == False or len(conf.seq_requisi) == 0:
			raise exceptions.Warning('No ha configurado la secuencia de Requisiciones')
		
		used_lots = self.lot_ids.mapped('lot_id').filtered(lambda x: x.requisition_id)
		if len(used_lots) > 0:
			msg = ''
			for item in used_lots:
				msg += '-> Lote: ' + item.name + ' con Requisicion: '+ item.requisition_id.name+'.\n'
			raise exceptions.Warning('Los siguientes lotes ya tienen orden de requisicion:\n'+msg)

		products = self.lot_ids.mapped('lot_id').mapped('product_id')
		if len(products) == 0:
			raise exceptions.Warning('No ha agregado Lotes en la Orden de Requisicion.')
		if len(products) > 1:
			raise exceptions.Warning('El producto de los Lotes agregados debe ser unico')
		
		lots = self.lot_ids.mapped('lot_id')
		lots.write({'requisition_id':self.id})
		for line in lots.mapped('line_ids').filtered(lambda x: not x.is_break): 
			stage_obj = self.env['glass.stage.record'].create({
				'user_id':self.env.uid,
				'date':(datetime.now()-timedelta(hours=5)).date(),
				'time':(datetime.now()-timedelta(hours=5)).time(),
				'stage':'requisicion',
				'lot_line_id':line.id,
			})
			line.requisicion=True
		self.write({
			'name':conf.seq_requisi.next_by_id(),
			'state':'confirm',
			'product_id':products[0].id,
		})

	@api.model
	def create(self,vals):
		if 'table_number' in vals:
			vals['table_number']=self.get_table_name(vals['table_number'])
		if 'lot_ids' in vals:
			for lote in vals['lot_ids']:
				lote_act = self.env['glass.lot'].browse(lote[2]['lot_id'])
				lote[2]['m2']=lote_act.total_area
				lote[2]['user_id']=lote_act.create_uid.id
				lote[2]['crystal_count']=len(lote_act.line_ids)
		return super(GlassRequisition,self).create(vals)

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

		if 'table_number' in vals:
			vals['table_number']=self.get_table_name(vals['table_number'])

		return super(GlassRequisition,self).write(vals)
		 
	@api.multi
	def get_table_name(self,table):
		if not table.isnumeric():
			raise UserError('El valor ingresado "'+table+'" no es valido,\nIngrese un numero entero.')
		if len(str(table)) > 6:
			raise UserError('El valor ingresado "'+table+'" excede el limite permitido (6 cifras).')
		return 'M' + table.rjust(6,'0')

	@api.one
	def cancel(self):
		for pick in self.picking_ids:
			pick.action_revert_done()
			pick.action_cancel()
		for lot in self.lot_ids.mapped('lot_id'):
			lot.requisition_id = False
			for line in lot.line_ids.filtered(lambda x:x.requisicion and not x.is_break):
				line.write({'requisicion':False})
				stages = line.stage_ids.filtered(lambda x: x.stage == 'requisicion')
				stages.unlink()
		self.raw_materials.write({'process':False})
		self.scraps.write({'process':False})
		self.return_scraps.write({'process':False})
		self.state='cancel'
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
			raise UserError(u'No es posible eliminar una Requisición que fue Confirmada')
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
		n,m,j,tpmp,tprt,tpdrt=0,0,0,0,0,0
		for l in self.lot_ids.mapped('lot_id'):
			n+=l.total_area
		for mp in self.picking_mp_ids.filtered(lambda x:x.state=='done').mapped('move_lines'):
			area = float(mp.product_id.uom_id.ancho*mp.product_id.uom_id.alto)/1000000
			m+=(mp.product_uom_qty*area)
			tpmp+=(mp.product_uom_qty*area)
		for rt in self.picking_rt_ids.filtered(lambda x:x.state=='done').mapped('move_lines'):
			val=float(rt.product_id.uom_id.ancho*rt.product_id.uom_id.alto)/1000000
			m+=rt.product_uom_qty*val
			tprt+=rt.product_uom_qty*val
		for drt in self.picking_drt_ids.filtered(lambda x:x.state=='done').mapped('move_lines'):
			val=float(drt.product_id.uom_id.ancho*drt.product_id.uom_id.alto)/1000000
			j+=drt.product_uom_qty*val			
			tpdrt+=drt.product_uom_qty*val

		self.required_area = n
		self.required_mp   = m
		self.merma         = (m-j)-n
		self.total_picking_mp  = tpmp
		self.total_picking_rt  = tprt
		self.total_picking_drt = tpdrt
		self.returned_area = j
		self.used_area     = m-j

	@api.one
	def get_picking(self,type_pick,motive):
		return self.env['stock.picking'].create({
				'picking_type_id': type_pick.id,
				'partner_id': None,
				'date': (datetime.now()-timedelta(hours=5)).date(),
				'fecha_kardex':(datetime.now()-timedelta(hours=5)).date(),
				'origin': self.name,
				'location_dest_id': type_pick.default_location_dest_id.id,
				'location_id': type_pick.default_location_src_id.id,
				'company_id': self.env.user.company_id.id,
				'einvoice_12': motive.id,
				})

	@api.multi
	def process(self):
		if len(self.picking_mp_ids) == 0 and len(self.picking_rt_ids) == 0:
			raise exceptions.Warning(u'Error:\nLa Orden de requisición debe tener por lo menos un Albarán de Materias primas o de Retazos')
		not_process = len(self.raw_materials.filtered(lambda x: not x.process))
		not_process += len(self.scraps.filtered(lambda x: not x.process))
		not_process += len(self.return_scraps.filtered(lambda x: not x.process))
		if not_process > 0:
			raise UserError(u'Existen lineas sin procesar.\nRemueva o procese dichas líneas')
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
		self.state='process'			

	@api.multi
	def transfer_picking(self,picking,ctx=None):
		try:
			picking.action_confirm()
			picking.force_assign()
		except UserError as e:
			raise UserError('No fue posible forzar la disponibilidad:\nPosible Causa:\n'+str(e))
		if ctx:
			action = picking.with_context({ctx:True}).do_new_transfer()
		else:
			action = picking.do_new_transfer()
		context,bad_execution,motive = None,None,None
		if type(action) == type({}):
			if action['res_model'] == 'stock.immediate.transfer':
				context = action['context']
				sit = self.env['stock.immediate.transfer'].with_context(context).create({'pick_id':picking.id})	
				try:
					if ctx:
						sit.with_context({ctx:True}).process()
					else:
						sit.process()
				except UserError as e:
					bad_execution,motive = picking.name,str(e)
		if bad_execution:
			raise UserError('No fue posible procesar los siguiente Picking: '+bad_execution+'\nPosible causa: '+motive)

	# Metodo para crear los move_lines
	@api.multi
	def create_move(self,picking,pick_type,product,quantity,uom=None):
		move = self.env['stock.move'].create({
			'name': product.name or '',
			'product_id': product.id,
			'product_uom': product.uom_id.id,
			'date': (datetime.now()-timedelta(hours=5)).date(),
			'date_expected': (datetime.now()-timedelta(hours=5)).date(),
			'location_dest_id':picking.location_dest_id.id,
			'location_id': picking.location_id.id,
			'picking_id': picking.id,
			'move_dest_id': False,
			'state': 'draft',
			'company_id': self.env.user.company_id.id,
			'picking_type_id': pick_type.id,
			'procurement_id': False,
			'origin': self.name,
			'route_ids': pick_type.warehouse_id and [(6, 0, [x.id for x in pick_type.warehouse_id.route_ids])] or [],
			'warehouse_id': pick_type.warehouse_id.id,
			'product_uom_qty': quantity,
		})
		return move[0]

	# MATERIAS PRIMAS:
	@api.multi
	def add_material(self):
		# materiales permitidos		
		conf = self.env['glass.order.config'].search([])[0]
		location = conf.picking_type_mp.default_location_src_id
		allowed = self.get_allowed_materials(self.product_id)
		wizard = self.env['requisition.worker.material.wizard'].create({
			'requisition_id':self.id,
		})
		for item in allowed:
			factor = float(item.uom_id.alto*item.uom_id.ancho)/1000000
			pieces = int(self.get_available(item.id,location.id)/factor)
			if pieces <= 0:
				continue
			line = self.env['requisition.worker.wizard.line'].create({
				'material_id':wizard.id,
				'product_id':item.id,
				'available':pieces,
			})
		return {
			'res_id':wizard.id,
			'name':'Agregar Material',
			'type': 'ir.actions.act_window',
			'res_model': 'requisition.worker.material.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}

	@api.multi
	def process_material(self):
		conf = self.env['glass.order.config'].search([])[0]
		type_mp = conf.picking_type_mp
		raw_materials_picking = self.get_picking(type_mp,conf.traslate_motive_mp)[0]
		raw_materials = self.raw_materials.filtered(lambda x: not x.process)
		if len(raw_materials) > 0:
			for item in raw_materials:
				self.create_move(raw_materials_picking,type_mp,item.product_id,item.quantity)
			self.transfer_picking(raw_materials_picking)
			self.picking_mp_ids |= raw_materials_picking
			raw_materials.write({'process':True})
		else:
			raise UserError('No hay lineas nuevas para procesar')
		
	# RETAZOS:
	@api.multi
	def add_scraps(self):
		# buscar si los materiales permitidos tienen un equivalente en retazo	
		conf = self.env['glass.order.config'].search([])[0]
		location = conf.picking_type_rt.default_location_src_id
		allowed = self.get_allowed_materials(self.product_id)
		gsm = self.env['glass.scrap.move'].search([('product_id','in',allowed.ids)])
		if len(gsm) == 0:
			raise UserError('No se han encontrado Productos de retazo para las Materias Primas Disponibles')
		wizard = self.env['requisition.worker.scraps.wizard'].create({
			'requisition_id':self.id,
		})
		for item in gsm.filtered(lambda x: x.quantity > 0):
			line = self.env['requisition.worker.wizard.line'].create({
				'scraps_id':wizard.id,
				'product_id':item.product_id.id,
				'width':item.width,
				'height':item.height,
				'available':item.quantity,
			})
		return {
			'res_id':wizard.id,
			'name':'Agregar Retazos',
			'type': 'ir.actions.act_window',
			'res_model': 'requisition.worker.scraps.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}

	@api.multi
	def process_scraps(self):
		conf = self.env['glass.order.config'].search([])[0]
		scraps = self.scraps.filtered(lambda x: not x.process)
		if len(scraps) > 0:
			type_rt = conf.picking_type_rt
			scraps_picking = self.get_picking(type_rt,conf.traslate_motive_rt)[0]
			for item in scraps:
				quantity = (float(item.width*item.height)/1000000)*item.quantity
				area = quantity
				# cantidad en unidad de medida del producto (plancha)
				if item.product_id.uom_id.ancho and item.product_id.uom_id.alto:
					t = float(item.product_id.uom_id.ancho*item.product_id.uom_id.alto)/1000000
					quantity = quantity/t
				else:
					raise Warning('La unidad de medida del producto '+ item.product_id.name + ' no tiene ancho y/o alto!')
				move = self.create_move(scraps_picking,type_rt,item.product_id,round(quantity,6))
				gsm = self.env['glass.scrap.move'].search([('product_id','=',item.product_id.id),('width','=',item.width),('height','=',item.height)])
				if any(gsm):
					qty = gsm.quantity
					gsm.write({'quantity': qty - item.quantity,})
				else:
					raise UserError('El Registro de retazos para '+item.product_id.name+' ha sido removido')
				record = self.env['glass.scrap.record'].create({
					'move_id':move.id,
					'product_id':item.product_id.id,
					'user_id':self.env.user.id,
					'area': area,
					'pieces':item.quantity,
					'scrap_move_id':gsm.id,
					'type_move':'out', # salida de retazos
				})
				move.scrap_record_id = record.id
			self.transfer_picking(scraps_picking,ctx='first_transaction')
			self.picking_rt_ids |= scraps_picking
			scraps.write({'process':True,})
		else:
			raise UserError('No hay lineas nuevas para procesar')

	# DEVOLUCION DE RETAZOS:
	@api.multi
	def add_return_scraps(self):		
		products = self.raw_materials.mapped('product_id') + self.scraps.mapped('product_id')# mat disponibles para devolver
		if len(products) == 0:
			raise UserError('No ha solicitado materias primas de las cuales devolver retazos')
		wizard = self.env['requisition.worker.scraps.return.wizard'].create({
			'requisition_id':self.id,
		})
		for item in products:
			line = self.env['requisition.worker.wizard.line'].create({
				'product_id':item.id,
				'scraps_return_id':wizard.id,
			})

		return {
			'res_id':wizard.id,
			'name':'Devolver Retazos',
			'type': 'ir.actions.act_window',
			'res_model': 'requisition.worker.scraps.return.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}

	@api.multi
	def process_return_scraps(self):
		conf = self.env['glass.order.config'].search([])[0]
		return_scraps = self.return_scraps.filtered(lambda x: not x.process)
		if len(return_scraps) > 0:
			type_drt    = conf.picking_type_drt
			scraps_return_picking = self.get_picking(type_drt,conf.traslate_motive_drt)[0]
			for item in return_scraps:
				quantity = ((float(item.width)*float(item.height))/1000000)*item.quantity
				area = quantity
				# cantidad en unidad de medida del producto (plancha)
				if item.product_id.uom_id.ancho and item.product_id.uom_id.alto:
					t = (float(item.product_id.uom_id.ancho)*float(item.product_id.uom_id.alto))/1000000
					quantity = quantity/t
				else:
					raise Warning('La unidad de medida del producto '+ item.product_id.name + ' no tiene ancho y/o alto!')
				move = self.create_move(scraps_return_picking,type_drt,item.product_id,round(quantity,4))
				gsm = self.env['glass.scrap.move'].search([('product_id','=',item.product_id.id),('width','=',item.width),('height','=',item.height)])
				if any(gsm):
					qty = gsm.quantity
					gsm.write({'quantity': qty + item.quantity,})
				else:
					gsm = self.env['glass.scrap.move'].create({
					'product_id':item.product_id.id, 
					'width':item.width,
					'height':item.height,
					'quantity':item.quantity,
					'location':conf.location_retazo.id,
					})
				record = self.env['glass.scrap.record'].create({
					'move_id':move.id,
					'product_id':item.product_id.id,
					'user_id':self.env.user.id,
					'area': area,
					'pieces':item.quantity,
					'scrap_move_id':gsm.id,
					'type_move':'in',
				})
				move.scrap_record_id = record.id
			self.transfer_picking(scraps_return_picking,ctx='first_transaction')
			self.picking_drt_ids |= scraps_return_picking
			return_scraps.write({'process':True,})
		else:
			raise UserError('No hay lineas nuevas para procesar')

	@api.multi
	def get_available(self,product,location):
		try:
			fiscal = self.env['main.parameter'].search([])[0].fiscalyear
		except IndexError as e:
			raise UserError(u'No se ha encontrado la configuración de Año Fiscal.')
		self.env.cr.execute("""
			select sum(stock_disponible) 
			from vst_kardex_onlyfisico_total
			where vst_kardex_onlyfisico_total.date >= '"""+str(fiscal)+"""-01-01'
			and vst_kardex_onlyfisico_total.date <= '"""+str(fiscal)+"""-12-31'
			and product_id = '"""+str(product)+"""'
			and ubicacion = '"""+str(location)+"""'
			group by product_id
		""")
		try:
			res = list(self.env.cr.fetchall()[0])[0]
		except IndexError as e:
			res = 0
		return res

class GlassRequisitionLineLot(models.Model):
	_name = 'glass.requisition.line.lot'

	lot_id = fields.Many2one('glass.lot','Lote')
	date=fields.Date('Fecha',default=(datetime.now()-timedelta(hours=5)).date())
	user_id=fields.Many2one('res.users','Usuario')
	m2 = fields.Float('M2',digits=(20,4))
	requisition_id = fields.Many2one('glass.requisition','requisition')
	crystal_count=fields.Integer(u'Numero de cristales')

	@api.onchange('lot_id')
	def onchangelot(self):
		self.m2 = self.lot_id.total_area
		self.date=self.lot_id.date
		self.user_id=self.lot_id.create_uid.id
		self.crystal_count=len(self.lot_id.line_ids)
