# -*- coding: utf-8 -*-
from odoo import fields, models,api,exceptions, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta

class GlassFurnaceOut(models.Model):
	_name='glass.furnace.out'
	_inherit = ['mail.thread']
	_order="date_out desc"

	name = fields.Char('Lote de Horno Salida',default="/")
	nro_crystal=fields.Integer('Nro. Cristales')
	total_m2=fields.Float('Total M2',digits=(12,4))
	e_percent=fields.Float('% de Eficiencia',digits=(12,4))
	state = fields.Selection([('draft','Borrador'),('process','En Proceso'),('done','Finalizado')],'Estado',default='draft')
	line_ids=fields.One2many('glass.furnace.line.out','main_id','Detalle')
	user_ingreso = fields.Many2one('res.users','Usuario Ingreso')
	date_ingreso = fields.Datetime('Fecha Ingreso')
	date_out=fields.Datetime('Fecha Salida')
	user_out = fields.Many2one('res.users','Usuario Salida')
	show_button = fields.Boolean('Mostrar Limpiar', compute='_get_show_button')

	@api.depends('line_ids')
	def _get_show_button(self):
		for rec in self:
			bad_lines = rec.line_ids.filtered(lambda x: x.lot_line_id.is_break)
			if len(bad_lines) > 0:
				rec.show_button = True
			else:
				rec.show_button = False

	@api.multi
	def remove_bad_lines(self):
		self.line_ids.filtered(lambda x: x.lot_line_id.is_break).unlink()
		return True

	@api.one
	def furnace_out(self):
		breaks = self.line_ids.filtered(lambda x: x.lot_line_id.is_break)
		msg = ''
		for item in breaks:
			msg += '-> %s - %s : Cristal Roto\n'%(item.lot_line_id.search_code,item.lot_line_id.nro_cristal)
		if msg != '':
			raise exceptions('No es posible procesar los siguientes cristales\n'+msg+u'Haga click en el botón limpiar para remover los cristales rotos.') 
		
		for line in self.line_ids:	
			self.env['glass.stage.record'].create({
					'user_id':self.env.uid,
					'date':(datetime.now()-timedelta(hours=5)).date(),
					'time':(datetime.now()-timedelta(hours=5)).time(),
					'stage':'templado',
					'lot_line_id':line.lot_line_id.id,
				})
			line.lot_line_id.is_used=True
			line.lot_line_id.templado=True
			line.lot_line_id.order_line_id.state = 'ended'

		self.write({'state':'done','user_out':self.env.uid,'date_out':(datetime.now()-timedelta(hours=5))})
		return True

class GlassFurnaceIn(models.TransientModel):
	_name = 'glass.furnace.in'
	line_in_ids = fields.One2many('glass.furnace.line.in','main_id')
	search_code = fields.Char('Producto', store=False)
	crystal_num = fields.Integer('Nro de cristales',compute='_get_crystal_num')
	message_erro = fields.Char('*',default='')

	@api.multi
	def get_element(self):
		wizard = self.create({})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_glass_furnace_in_form' % module)
		return {
			'name':'Ingreso a Horno',
			'res_id':wizard.id,
			'type': 'ir.actions.act_window',
			'res_model': 'glass.furnace.in',
			'view_id': view.id,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
			}

	@api.depends('line_in_ids')
	def _get_crystal_num(self):
		for rec in self:
			rec.crystal_num = len(rec.line_in_ids)

	@api.onchange('search_code')
	def onchangecode(self):
		if self.search_code and self._origin.id:
			line=self.env['glass.lot.line'].search([('search_code','=',self.search_code)])
			self.search_code = self.message_erro = ''
			if len(line)>0:
				if line.templado:
					self.message_erro="El cristal ya fue registrado en la etapa Templado"
					return
				# restriccion quitada temporalmente
				# if not line.lavado:
				# 	self.message_erro="El cristal no tiene la etapa LAVADO"
				# 	return
				existe_act = line[0]
				this = self.browse(self._origin.id)
				if existe_act.id in this.line_in_ids.mapped('lot_line_id').ids:
					self.message_erro="El cristal seleccionado ya fue registrado en este ingreso a horno"
					return
				new_line = self.env['glass.furnace.line.in'].create({
					'main_id': this.id,
					'lot_line_id':existe_act.id,
					'order_number':len(this.line_in_ids) + 1
				})
			else:
				self.message_erro="Codigo de busqueda no encontrado!"
				return
		else:
			return
		return {'value':{'line_in_ids':this.line_in_ids.ids}}

	@api.multi
	def generate_furnace_lot(self):
		try:
			conf = self.env['glass.order.config'].search([])[0]
		except IndexError as e:
			raise UserError(u'No se encontraron los valores de configuración de produccion')
		if len(self.line_in_ids) == 0:
			raise exceptions.Warning('No ha ingresado Cristales.')
		
		breaks = self.line_in_ids.filtered(lambda x: x.lot_line_id.is_break)
		furnace = self.line_in_ids.filtered(lambda x: x.lot_line_id.horno)
		msg = ''
		for bad in breaks:
			msg+='-> %s - %s :Roto\n'%(bad.lot_line_id.search_code,bad.lot_line_id.nro_cristal)
		for bad in furnace:
			msg+='-> %s - %s :En Horno\n'%(bad.lot_line_id.search_code,bad.lot_line_id.nro_cristal)
		if msg != '':
			raise exceptions.Warning('Los siguientes cristales no pueden procesarse:\n'+msg)
		
		area = sum(self.line_in_ids.mapped('area'))
		new_furnace_lot = self.env['glass.furnace.out'].create({
			'date_out':datetime.now()-timedelta(hours=5),
			'user_ingreso':self.env.uid,
			'date_ingreso':datetime.now()-timedelta(hours=5),
			'e_percent':(area*100)/conf.furnace_area,
			'name':conf.seq_furnace.next_by_id(),
			'state':'process',
			'total_m2':area,
			'nro_crystal':self.crystal_num,
		})

		for i,line in enumerate(self.line_in_ids):
			self.env['glass.furnace.line.out'].create({
				'main_id': new_furnace_lot.id,
				'order_number':i,
				'lot_id':line.lot_line_id.lot_id.id,
				'lot_line_id':line.lot_line_id.id,
				'crystal_number':line.lot_line_id.nro_cristal,
				'base1':line.lot_line_id.base1,
				'base2':line.lot_line_id.base2,
				'altura1':line.lot_line_id.altura1,
				'altura2':line.lot_line_id.altura2,
				'area':line.lot_line_id.area,
				'partner_id':line.lot_line_id.order_prod_id.partner_id.id,
				'obra':line.lot_line_id.order_prod_id.obra,
			})
			self.env['glass.stage.record'].create({
				'user_id':self.env.uid,
				'date':(datetime.now()-timedelta(hours=5)).date(),
				'time':(datetime.now()-timedelta(hours=5)).time(),
				'stage':'horno',
				'lot_line_id':line.lot_line_id.id,
				})
			line.lot_line_id.horno=True
		return self.get_element()

class GlassFurnaceLineIn(models.TransientModel):
	_name = 'glass.furnace.line.in'
	main_id = fields.Many2one('glass.furnace.in')
	lot_line_id = fields.Many2one('glass.lot.line')
 	order_number = fields.Integer('Nro de Orden')
	crystal_number = fields.Char(related='lot_line_id.nro_cristal')
	base1 = fields.Integer(related='lot_line_id.base1')
	base2 = fields.Integer(related='lot_line_id.base2')
	altura1 = fields.Integer(related='lot_line_id.altura1')
	altura2 = fields.Integer(related='lot_line_id.altura2')
	area = fields.Float(related='lot_line_id.area')
	

class GlassFurnaceLineOut(models.Model):
	_name='glass.furnace.line.out'

	#_rec_name="lot_line_id"
	main_id = fields.Many2one('glass.furnace.out')
	lot_id = fields.Many2one('glass.lot','Lote')
	lot_line_id = fields.Many2one('glass.lot.line',u'Línea de lote')
	order_number = fields.Integer(u'Nro. Orden')
	crystal_number = fields.Char('Nro. Cristal')
	base1 = fields.Integer("Base1 (L 4)")
	base2 = fields.Integer("Base2 (L 2)")
	altura1 = fields.Integer("Altura1 (L 1)")
	altura2 = fields.Integer("Altura2 (L 3)")
	area = fields.Float(u'Área M2',digits=(20,4))
	partner_id = fields.Many2one('res.partner',string='Cliente',)
	obra = fields.Char(string='Obra')
	etiqueta = fields.Boolean(string='Etiqueta')
	is_used = fields.Boolean(string='Usado', default=False)
	is_break = fields.Boolean(related='lot_line_id.is_break',string='Roto')

	@api.multi
	def reset_label(self):
		self.write({'etiqueta':False})
		return True