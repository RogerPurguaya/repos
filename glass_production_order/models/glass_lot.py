# -*- coding: utf-8 -*-

from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime

# class GlassTable(models.Model):
# 	_name='glass.table'

# 	name = fields.Char('Lote')
# 	date =fields.Date('Fecha',default=datetime.now())
# 	lot_ids = fields.One2many('glass.lot','table_id','Lotes')

class GlassLot(models.Model):
	_name='glass.lot'
	_inherit = ['mail.thread']
	_order="id desc"

	name = fields.Char('Lote', default='/')
	state = fields.Selection([('draft','Nuevo'),('cancel','Cancelado'),('done','Emitido')],'Estado',track_visibility='always',default='draft')
	date = fields.Date('Fecha',default=datetime.now())
	product_id=fields.Many2one('product.product','Producto')
	total_pza = fields.Integer('Total Piezas',compute="_countlines")
	total_area = fields.Float('Área Total',compute="_totalarea",digits=(20,4))
	#table_id = fields.Many2one('glass.table','Mesa')
	line_ids=fields.One2many('glass.lot.line','lot_id','Detalle')
	crystal_count=fields.Integer(u'Número de cristales',compute="getcrystalcount")
	user_id = fields.Many2one('res.users','Responsable')
	optimafile=fields.Binary('Archivo OPTIMA')
	file_name = fields.Char(string='File Name', compute='_get_file_name')
	requisition_id = fields.Many2one('glass.requisition',string="Requisicion")

	@api.depends('name')
	def _get_file_name(self):
		for record in self:
			ext = self.env['glass.order.config'].search([],limit=1).optimization_ext
			record.file_name = '%s.%s'%(record.name.rjust(7,'0'),(ext or 'ext'))

	@api.multi
	@api.depends('name', 'product_id')
	def name_get(self):
		result = []
		for lote in self:
			name = lote.name + ' ' + lote.product_id.name
			result.append((lote.id, name))
		return result

	@api.one
	def unlink(self):
		if self.state in ('cancel','done'):
			raise UserError(u'No se puede eliminar en los estados: Cancelado o Emitida')		
		return super(GlassLot,self).unlink()

	@api.one
	def optimize_lot(self):
		for line in self.line_ids:
			line.order_line_id.order_id.state="process"
		return True

	@api.one
	def getcrystalcount(self):
		crystal_count=len(self.line_ids)

	def cancel_lot(self):
		self.ensure_one()
		lines = self.line_ids
		lines.mapped('order_line_id').write({'is_used':False})
		lines.unlink()
		self.state='cancel'
		return True

	@api.one
	def _totalarea(self):	
		self.total_area = sum(self.line_ids.mapped('area'))

	@api.one
	def _countlines(self):
		self.total_pza=len(self.line_ids)

	@api.one
	def validate_lot(self):
		config_data = self.env['glass.order.config'].search([])[0]
		if self.name=='/':
			newname = config_data.seq_lot.next_by_id()
			self.update({'name':newname})
		self.write({'state':'done'})
		for line in self.line_ids:
			line.order_line_id.is_used = True
		return True

	@api.onchange('line_ids')
	def onchange_lines(self):
		self.total_pza = len(self.line_ids)

	@api.multi
	def showpool(self):
		# search_view_ref = self.env.ref('account.view_account_invoice_filter', False)
		form_view_ref = self.env.ref('glass_production_order.view_glass_pool_wizard_form', False)
		# tree_view_ref = self.env.ref('account.invoice_tree', False)
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_glass_pool_wizard_form' % module)
		data = {
			'name': _('Pool de pedidos'),
			'context': self._context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'glass.pool.wizard',
			'view_id': view.id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		} 
		return data

class GlassLotLine(models.Model):
	_name='glass.lot.line'

	lot_id = fields.Many2one('glass.lot','Lote')
	product_id=fields.Many2one('product.product','Producto')
	calc_line_id = fields.Many2one('glass.sale.calculator.line',copy=False)
	order_line_id = fields.Many2one('glass.order.line')
	nro_cristal = fields.Char(u"Número de Cristal",size=10)
	order_prod_id = fields.Many2one('glass.order',related='order_line_id.order_id',string="OP",store=True)
	order_date_prod = fields.Date('Fecha OP',related='order_prod_id.date_production')
	search_code = fields.Char(u'Código de búsqueda',index=True)
	base1 = fields.Integer("Base1 (L 4)")
	base2 = fields.Integer("Base2 (L 2)")
	altura1 = fields.Integer("Altura1 (L 1)")
	altura2 = fields.Integer("Altura2 (L 3)")
	area = fields.Float(u'Área M2',digits=(12,4))
	measures = fields.Char('Medidas',related='calc_line_id.measures',store=True)
	page_number = fields.Integer(u"Nro. Pág.")
	
	optimizado = fields.Boolean('Optimizado',compute='_compute_checked_stages',store=True)
	corte = fields.Boolean('Corte',compute='_compute_checked_stages',store=True)
	pulido = fields.Boolean('Pulido',compute='_compute_checked_stages',store=True)
	lavado = fields.Boolean('Lavado',compute='_compute_checked_stages',store=True)
	entalle = fields.Boolean('Entalle',compute='_compute_checked_stages',store=True)
	horno = fields.Boolean('Horno',compute='_compute_checked_stages',store=True)
	templado = fields.Boolean('Templado',compute='_compute_checked_stages',store=True)
	insulado = fields.Boolean('Insulado',compute='_compute_checked_stages',store=True)
	producido = fields.Boolean('Producido',compute='_compute_checked_stages',store=True)
	ingresado = fields.Boolean('Ingresado',compute='_compute_checked_stages',store=True)
	entregado = fields.Boolean('Entregado',compute='_compute_checked_stages',store=True)
	arenado = fields.Boolean('Arenado',compute='_compute_checked_stages',store=True)
	comprado = fields.Boolean('Comprado',compute='_compute_checked_stages',store=True)
	
	is_break = fields.Boolean('Roto',compute='_compute_break_crystal',store=True)
	stage_ids = fields.One2many('glass.stage.record','lot_line_id',string='Etapas')
	
	descuadre = fields.Char("Descuadre",size=7)
	requisicion = fields.Boolean("Requisición")
	laminado = fields.Boolean("Laminado")

	is_service = fields.Boolean('Es servicio') # ?
	type_prod = fields.Char('tipoproducto') # ?
	image_glass = fields.Binary("imagen",related="calc_line_id.image") #?
	merma = fields.Float('Merma',digist=(12,4)) #?
	#page_glass = fields.Binary(u"Página")
	#location = fields.Many2one(related='order_line_id.custom_location',string='Ubicacion') 
	#warehouse = fields.Char(related='location.location_code.display_name',string='Almacen')
	_rec_name="search_code"

	@api.depends('stage_ids.done')
	def _compute_checked_stages(self):
		static_stg = ('optimizado','corte','pulido','lavado','entalle','horno','templado','producido','insulado','ingresado','entregado','arenado','comprado')
		for line in self:
			done_states = line.stage_ids.filtered('done')
			for stg in static_stg:
				line[stg] = done_states.filtered(lambda s: s.stage_id.name==stg)
			# line.optimizado = bool(done_states.filtered(lambda s: s.stage_id.name=='optimizado'))
			# line.corte      = bool(done_states.filtered(lambda s: s.stage_id.name=='corte'))
			# line.pulido     = bool(done_states.filtered(lambda s: s.stage_id.name=='pulido'))
			# line.lavado     = bool(done_states.filtered(lambda s: s.stage_id.name=='lavado'))
			# line.entalle    = bool(done_states.filtered(lambda s: s.stage_id.name=='entalle'))
			# line.horno      = bool(done_states.filtered(lambda s: s.stage_id.name=='horno'))
			# line.templado   = bool(done_states.filtered(lambda s: s.stage_id.name=='templado'))
			# line.insulado   = bool(done_states.filtered(lambda s: s.stage_id.name=='insulado'))
			# line.ingresado  = bool(done_states.filtered(lambda s: s.stage_id.name=='ingresado'))
			# line.entregado  = bool(done_states.filtered(lambda s: s.stage_id.name=='entregado'))
			# line.arenado    = bool(done_states.filtered(lambda s: s.stage_id.name=='arenado'))
			# line.comprado   = bool(done_states.filtered(lambda s: s.stage_id.name=='comprado'))

	@api.depends('stage_ids.break_stage_id')
	def _compute_break_crystal(self):
		break_stage = self.env['glass.order.config'].search([],limit=1).break_stage_id
		if not break_stage:
			raise UserError(u'No se ha encontrado la etapa de rotura por defecto.\nVaya a parámetros de producción->Etapa de rotura. para configurarla.')
		for line in self:
			line.is_break=bool(line.stage_ids.filtered(lambda x: x.stage_id==break_stage and x.done))

	@api.multi
	def retire_lot_line(self):
		self.ensure_one()
		if self.corte:
			raise UserError(u'No se puede retirar si a pasado la etapa de corte')		
		rid =self.lot_id.id
		self.order_line_id.write({
			#'last_lot_line':self.id,
			'glass_break':False,
			'lot_line_id':False,
			'is_used':False,
			'retired_user':self.env.uid,
			'retired_date':datetime.now(),
		})
		self.unlink()
		module = __name__.split('addons.')[1].split('.')[0]
		return {
			'name': u'Lotes de producción',
			'res_id':rid,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'glass.lot',
			'view_id': self.env.ref('%s.view_glass_lot_form'%module).id,
			'type': 'ir.actions.act_window',
			'target': 'current',
		} 

	@api.constrains('stage_ids')
	def _verify_unique_stages(self):
		for rec in self:
			names = [stage.stage_id.name for stage in rec.stage_ids]
			if len(names) > len(set(names)):
				raise ValidationError('Existen etapas duplicadas para el cristal %s Número: %s'%(rec.product_id.name,rec.nro_cristal))

	@api.model
	def create(self,values):
		# create required stages
		t = super(GlassLotLine,self).create(values)
		req_stages = t._get_requested_stages()
		if any(req_stages):
			stages = self.env['glass.stage'].search([('name','in',req_stages)])
			for stage in stages:
				t._add_stage(stage)
		return t

	def _get_requested_stages(self):
		self.ensure_one()
		# get requested stages from calculator
		# etapas definidas en calculadora ( no es buena idea ponerlo en estático pero
		# dado que no hay prisa queda asi esa vaina):
		stages = ['pulido','lavado','entalle','arenado']
		if not self.calc_line_id.polished_id:
			stages.remove('pulido')
		if not self.calc_line_id.arenado:
			stages.remove('arenado')
		if not self.calc_line_id.entalle:
			stages.remove('entalle')
		if not self.calc_line_id.lavado:
			stages.remove('lavado')
		return stages

	# solo agrega una etapa por realizarse
	def _add_stage(self,stage):
		for line in self:
			line.write({'stage_ids':[(0,0,line._prepare_record_stage_vals(stage))]})
	
	def register_stage(self,stage,break_info=False):
		"""break_info debe ser un dict con posibles keys en break_motive,break_stage_id,break_note"""
		StageObj = self.env['glass.stage']
		stage = stage if isinstance(stage,StageObj.__class__) else StageObj.search([('name','=',stage)])
		bad_items = []
		ctx = self._context
		for line in self:
			if ctx.get('force_register') is None and stage.name not in line._get_requested_stages():
				bad_items.append(u'Etapa de %s no fue solicitada para el cristal: %s.'%(stage.name,line.search_code))
			# ver si la etapa ya existe y hace falta realizarla
			else:
				existing = line.stage_ids.filtered(lambda x: x.stage_id==stage)
				if existing.done:
					bad_items.append(u'Etapa: %s Cristal: %s.'%(stage.name,line.search_code))
				elif existing:
					existing.write({'done':True,'user_id':self.env.uid,'date':datetime.now()})
				else:
					# solo si se fuerza el registro
					new_vals = self._prepare_record_stage_vals(stage,done=True)
					if break_info:
						new_vals.update(break_info)
					line.stage_ids = [(0,0,new_vals)]
		if any(bad_items):
			error_msg = u'No fue posible registrar la(s) etapa(s), Detalle:\n'+'\n'.join(bad_items)
			if ctx.get('get_error_msg'):
				return error_msg
			else:
				raise UserError(error_msg)
		#self._compute_checked_stages()
		return True

	def _prepare_record_stage_vals(self,stage,done=False):
		return {
			'user_id':self.env.uid,
			'stage_id':stage.id,
			'lot_line_id':self.id,
			'date':datetime.now(),
			'done':done,
		}