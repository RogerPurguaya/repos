# -*- coding: utf-8 -*-
from odoo import fields, models,api,exceptions, _
from odoo.exceptions import UserError
from datetime import datetime
from functools import reduce

# Seguimiento a la produccion en almacen
class Glass_tracing_Production_Stock(models.TransientModel):
	_name='glass.tracing.production.stock'
	_rec_name = 'titulo'
	titulo = fields.Char(default='Seguimiento de Produccion Almacen')
	order_id = fields.Many2one('glass.order',string='Orden')
	customer_id = fields.Many2one('res.partner',string='Cliente')
	invoice_id = fields.Many2one('account.invoice',string='Factura')
	date_ini = fields.Date('Fecha Inicio')
	date_end = fields.Date('Fecha Fin')
	line_ids = fields.One2many('tracing.production.stock.line.lot','parent_id','Lineas')
	filter_field = fields.Selection([('all','Todos'),('pending','Pendientes'),('produced','Producidos'),('to inter','Por ingresar'),('to deliver','Por Entregar'),('expired','Vencidos')],string='Filtro',default='all')
	search_param = fields.Selection([('glass_order','Orden de Produccion'),('invoice','Factura'),('customer','Cliente')],default='glass_order',string='Busqueda por')
	show_breaks = fields.Boolean('Mostrar Rotos')
	total_area = fields.Float('Total M2',compute='_get_total_area',digits=(12,4))
	count_total_crystals = fields.Integer('Nro Cristales', compute='_get_count_crystals')
	show_customer = fields.Many2one('res.partner',string='Cliente', compute='_get_show_customer')
	show_invoice = fields.Many2one('account.invoice',string='Factura', compute='_get_show_invoice')

	total_area_breaks = fields.Float('Total Rotos M2',compute='_get_total_area_breaks',digits=(12,4))
	count_total_breaks = fields.Integer('Nro Rotos',compute='_get_count_breaks')
	percentage_breaks = fields.Float('Porcentage de rotos',compute='_get_percentage_breaks') 
	tot_templado=fields.Integer('Templado')
	tot_arenado=fields.Integer('Arenado')
	tot_ingresado=fields.Integer('Ingresado')
	tot_entregado=fields.Integer('Entregado')
	for_delivery = fields.Integer('Cristales por entregar',compute='_get_for_delivery')

	@api.depends('search_param','customer_id','invoice_id','order_id')
	def _get_show_customer(self):
		for rec in self:
			if rec.search_param == 'glass_order' and rec.order_id:
				rec.show_customer = rec.order_id.partner_id.id
			elif rec.search_param == 'invoice' and rec.invoice_id:
				rec.show_customer = rec.invoice_id.partner_id.id
			elif rec.search_param == 'customer' and rec.customer_id:
				rec.show_customer = rec.customer_id.id
			else:
				rec.show_customer = False

	@api.depends('search_param','customer_id','invoice_id','order_id')
	def _get_show_invoice(self):
		for rec in self:
			if rec.search_param == 'glass_order' and rec.order_id.invoice_ids:
				rec.show_invoice = rec.order_id.invoice_ids[0].id
			elif rec.search_param == 'invoice' and rec.invoice_id:
				rec.show_invoice = rec.invoice_id.id
			elif rec.search_param == 'customer' and rec.customer_id:
				rec.show_invoice = False
			else:
				rec.show_invoice = False

	@api.depends('line_ids')
	def _get_total_area(self):
		for rec in self:
			areas = rec.line_ids.mapped('lot_line_id').filtered(lambda x:not x.is_break).mapped('area')
			rec.total_area = sum(areas)

	@api.depends('line_ids')
	def _get_count_crystals(self):
		for rec in self:
			rec.count_total_crystals = len(rec.line_ids.mapped('lot_line_id').filtered(lambda x:not x.is_break))

	@api.depends('line_ids')
	def _get_total_area_breaks(self):
		for rec in self:
			line_ids = rec.line_ids.mapped('lot_line_id').filtered(lambda x: x.is_break)
			rec.total_area_breaks=sum(line_ids.mapped('area'))

	@api.depends('line_ids')
	def _get_count_breaks(self):
		for rec in self:
			rec.count_total_breaks = len(rec.line_ids.mapped('lot_line_id').filtered(lambda x: x.is_break))

	@api.depends('total_area','total_area_breaks')
	def _get_percentage_breaks(self):
		for rec in self:
			if rec.total_area > 0:
				rec.percentage_breaks=(rec.total_area_breaks/rec.total_area)*100
			else:
				rec.percentage_breaks=0
	
	@api.depends('line_ids')
	def _get_for_delivery(self):
		for rec in self:
			rec.for_delivery = len(rec.line_ids.mapped('lot_line_id').filtered(lambda x: not x.entregado and not x.is_break))

	@api.multi
	def makelist(self):
		self.ensure_one()
		self.env['tracing.production.stock.line.lot'].search([]).unlink()

		lines=[]
		if self.invoice_id and self.search_param == 'invoice':
			invoice_lines = self.invoice_id.invoice_line_ids
			sale_order_lines = invoice_lines.mapped('sale_line_ids')
			sale_order = sale_order_lines.mapped('order_id')
			if len(set(sale_order)) == 1:
				lines = sale_order.op_ids.mapped('line_ids.lot_line_id')
				aux_lines = sale_order.op_ids.mapped('line_ids')
				lines = self._get_data(lines)
			if self.show_breaks:
				glass_breaks = self.env['glass.lot.line'].with_context(active_test=False).search([('order_line_id','in',aux_lines.ids),('is_break','=',True)])
				lines += glass_breaks

		elif self.order_id and self.search_param == 'glass_order':
			lines = self.order_id.line_ids.filtered('lot_line_id').mapped('lot_line_id')
			lines = self._get_data(lines)
			if self.show_breaks:
				glass_breaks = self.env['glass.lot.line'].with_context(active_test=False).search([('order_line_id','in',self.order_id.line_ids.ids),('is_break','=',True)])
				lines += glass_breaks

		elif self.customer_id and self.search_param == 'customer':
			sale_orders = self.env['sale.order'].search([('partner_id','=',self.customer_id.id)])
			lines = sale_orders.mapped('op_ids.line_ids').mapped('lot_line_id')
			lines = self._get_data(lines)
			if self.show_breaks:
				glass_breaks = self.env['glass.lot.line'].with_context(active_test=False).search([('order_line_id','in',sale_orders.mapped('op_ids.line_ids').ids),('is_break','=',True)])
				lines += glass_breaks

		if len(lines)==0:
			raise exceptions.Warning(u'NO SE HA ENCONTRADO INFORMACIÓN.\nEs posible que los cristales aun no hayan iniciado el proceso de producción')

		for line in lines:
			self.env['tracing.production.stock.line.lot'].create({
				'parent_id':self.id,
				'order_id':line.order_prod_id.id,
				'lot_line_id':line.id,
				'customer_id':line.order_prod_id.partner_id.id,
				'embalado':False,
				'decorator':'break' if line.is_break else 'default',
				})
		lines = list(filter(lambda x: not x.is_break,lines))
		self.write({
		'tot_templado' :len(list(filter(lambda x:x.templado,lines))),
		'tot_ingresado':len(list(filter(lambda x:x.ingresado,lines))),
		'tot_entregado':len(list(filter(lambda x:x.entregado,lines))),
		'tot_arenado'  :len(list(filter(lambda x:x.arenado,lines))),
		})
		return True

	@api.multi
	def _get_data(self,lot_lines):
		if self.filter_field:
			if self.filter_field == 'all':
				pass
			elif self.filter_field == 'pending':
				lot_lines = lot_lines.filtered(lambda x:x.templado==False)
			elif self.filter_field == 'produced':
				lot_lines = lot_lines.filtered(lambda x:x.templado==True)
			elif self.filter_field == 'to inter':
				lot_lines = lot_lines.filtered(lambda x:x.templado==True and x.ingresado==False)
			elif self.filter_field == 'to deliver':
				lot_lines = lot_lines.filtered(lambda x:x.ingresado==True and x.entregado==False)
			elif self.filter_field == 'expired':
				now = datetime.now().date()
				lot_lines = lot_lines.filtered(lambda x: self._str2date(x.order_prod_id.date_delivery) < now and x.templado == False)
		if self.date_ini and self.date_end and self.search_param == 'customer':
			start = self._str2date(self.date_ini)
			end = self._str2date(self.date_end)
			lot_lines = lot_lines.filtered(lambda x: self._str2date(x.order_date_prod) < end and self._str2date(x.order_date_prod) > start)
		if not self.show_breaks:
			lot_lines = lot_lines.filtered(lambda x: not x.is_break)
		return list(set(lot_lines))

	def _str2date(self,string):
		return datetime.strptime(string,"%Y-%m-%d").date()

class Tracing_Production_Stock_Line_Lot(models.TransientModel):
	_name = 'tracing.production.stock.line.lot'

	parent_id = fields.Many2one('glass.tracing.production.stock','Main')
	order_id = fields.Many2one('glass.order','Orden produccion')
	lot_line_id = fields.Many2one('glass.lot.line','Linea de lote')
	product_name = fields.Char('Producto',related='lot_line_id.order_line_id.product_id.name')
	customer_id = fields.Many2one('res.partner','Cliente')
	crystal_number = fields.Char(related='lot_line_id.nro_cristal')
	# base1  =fields.Integer(related='lot_line_id,base1')
	# base2  =fields.Integer(related='lot_line_id,base2')
	# altura1=fields.Integer(related='lot_line_id,altura1')
	# altura2=fields.Integer(related='lot_line_id,altura2')
	measures = fields.Char(related='lot_line_id.measures')
	arenado  = fields.Boolean(related='lot_line_id.arenado')
	embalado = fields.Boolean('Embalado')
	templado = fields.Boolean(related='lot_line_id.templado')
	ingresado= fields.Boolean(related='lot_line_id.ingresado') 
	entregado= fields.Boolean(related='lot_line_id.entregado')
	producido = fields.Boolean(related='lot_line_id.producido') 
	decorator = fields.Selection([('default','default'),('break','break'),('without_lot','without_lot')],default='default')
	is_break = fields.Boolean(related='lot_line_id.is_break')
	location_apt = fields.Char(string=u'Ubicación APT',compute='_get_location')

	@api.depends('lot_line_id')
	def _get_location(self):
		conf = self.env['glass.order.config'].search([])[0].apt_location_id
		for rec in self:
			loc = rec.lot_line_id.order_line_id.locations.filtered(lambda x: x.location_code.id == conf.id)
			if any(loc):
				rec.location_apt = loc[0].name
			else:
				rec.location_apt = ''

	def show_detail_tracing_line(self):
		module = __name__.split('addons.')[1].split('.')[0]
		wizard = self.env['show.detail.tracing.line.wizard'].create({'lot_line_id':self.lot_line_id.id})
		return{
			'name': 'Detalle de Seguimiento',
			'res_id': wizard.id,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'show.detail.tracing.line.wizard',
			'view_id': self.env.ref('%s.show_detail_tracing_line_wizard_form'%module).id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}