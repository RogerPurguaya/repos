# -*- coding: utf-8 -*-

from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta,time
from decimal import *
from pyPdf import PdfFileReader,PdfFileWriter
from StringIO import StringIO
import base64,os,tempfile,sys
from subprocess import Popen, PIPE
from pdf2image import convert_from_path

class GlassOrder(models.Model):
	_name = 'glass.order'
	_inherit = ['mail.thread']
	_order = "id desc"

	name = fields.Char(u'Orden de producción',default='/')
	sale_order_id = fields.Many2one('sale.order', 'Pedido de venta',readonly=True)
	invoice_id = fields.Many2one('account.invoice','Documento',readonly=True)
	partner_id = fields.Many2one('res.partner', 'Cliente', related="sale_order_id.partner_id",readonly=True,store=True)
	delivery_department=fields.Char(u'Departamento', related="sale_order_id.partner_shipping_id.state_id.name")
	delivery_province=fields.Char(u'Provincia', related="sale_order_id.partner_shipping_id.province_id.name")
	delivery_street=fields.Char(u'Dirección Entrega', related="sale_order_id.partner_shipping_id.street")
	date_sale_order = fields.Datetime('Fecha de pedido de venta',related='sale_order_id.date_order')
	comercial_area=fields.Selection([('distribucion',u'Distribución'),('obra','Obra'),('proyecto','Proyecto')],u'Área Comercial' )
	obra =fields.Char('Obra')
	date_order = fields.Datetime('Fecha Emisión',default=datetime.now()-timedelta(hours=5))
	date_production = fields.Date(u'Fecha de Producción',track_visibility='onchange')
	date_send = fields.Date(u'Fecha de Despacho',track_visibility='onchange')
	date_delivery = fields.Date(u'Fecha de Entrega',track_visibility='onchange')
	warehouse_id = fields.Many2one('stock.warehouse',u'Almacén Despacho',compute="getwarehouse")
	seller_id = fields.Many2one('res.users','Vendedor',related='sale_order_id.user_id',store=True)
	corrected = fields.Boolean('Corregido')
	observ = fields.Text('Observaciones')
	state = fields.Selection([
		('draft','Generada'),
		('confirmed','Emitida'),
		('process','En Proceso'),
		('ended','Finalizada'),
		('delivered','Despachada'),
		('returned','Devuelta'),], 'Estado',default='draft',track_visibility='onchange')
	sale_lines = fields.One2many(related='sale_order_id.order_line')
	line_ids = fields.One2many('glass.order.line','order_id',u'Líneas a producir')
	total_area = fields.Float(u'Metros',compute="_gettotals",digits=(20,4))
	total_peso = fields.Float("Peso",compute="_gettotals",digits=(20,4))
	total_pzs = fields.Float("Total Pzs",compute="_gettotals")
	sketch = fields.Binary('Croquis')
	croquis_path = fields.Char(string='Ruta de Croquis')
	file_name = fields.Char("File Name")
	reference_order = fields.Char(related='sale_order_id.reference_order',store=True)
	editable_croquis = fields.Boolean('editar croquis',default=True)
	invoice_count = fields.Integer(string='# of Invoices', related='sale_order_id.invoice_count', readonly=True)
	invoice_ids = fields.Many2many("account.invoice", string='Invoices', related="sale_order_id.invoice_ids", readonly=True,track_visibility='onchange')
	invoice_status = fields.Selection(related='sale_order_id.invoice_status',string=u'Estado de Facturación', store=True,readonly=True)
	destinity_order = fields.Selection([('local','En la ciudad'),('external','En otra ciudad')],u'Lugar de entrega',default="local")
	send2partner=fields.Boolean('Entregar en ubicacion del cliente',default=False)
	in_obra = fields.Boolean('Entregar en Obra')

	@api.one
	def endedop(self):
		for line in self.line_ids:
			line.state='ended'
		self.state="ended"
		return True

	@api.one
	def unlink(self):
		if self.state in ('draft'):
			super(GlassOrder,self).unlink()
		else:
			raise UserError(u'No se puede eliminar una Orden de Producción en los estados: Emitida, En proceso, Finalizada o Despachada')		

	@api.one
	def optimizar(self):
		self.state="process"
		return True

	@api.one
	def save_pdf(self):
		self.editable_croquis=False
		return True		

	@api.multi
	def action_view_invoice(self):
		invoices = self.mapped('invoice_ids')
		action = self.env.ref('account.action_invoice_tree1').read()[0]
		if len(invoices) > 1:
			action['domain'] = [('id', 'in', invoices.ids)]
		elif len(invoices) == 1:
			action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
			action['res_id'] = invoices.ids[0]
		else:
			action = {'type': 'ir.actions.act_window_close'}
		return action

	@api.multi
	def remove_order(self):
		module = __name__.split('addons.')[1].split('.')[0]
		return {
			'name': 'Devolver Orden de Produccion',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'glass.remove.order',
			'view_id': self.env.ref('%s.glass_remove_order_form_view'%module).id,
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': {'order_id':self.id,'default_order_name':self.name},
		} 

	@api.one
	def getwarehouse(self):
		if self.sale_order_id:
			self.warehouse_id = self.sale_order_id.warehouse_id.id

	@api.one
	def _gettotals(self):
		ta=tp=n=0
		lines = self.line_ids.filtered(lambda x: x.state != 'cancelled')
		if len(lines) > 0:
			ta = sum(lines.mapped('area'))
			tp = sum(lines.mapped('peso'))
		self.total_area = ta
		self.total_peso = tp
		self.total_pzs  = len(lines)

	@api.multi
	def show_sketch(self):
		vals = {}
		wizard = self.env['add.sketch.file'].sudo()
		try:
			with open(self.croquis_path,"rb") as pdf_file:
				vals = {'sketch': pdf_file.read().encode("base64")}
		except TypeError as e:
			print(u'Path does not exist!')
			vals = {'message': 'Archivo Croquis removido o no encontrado!',}
		except IOError as e:
			print(u'Pdf file not found or not available!')
			vals = {'message': 'Archivo Croquis removido o no encontrado!',}
		wizard = wizard.create(vals)

		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.change_sketch_file_view_form' % module)
		return {
			'name':'Ver Croquis',
			'res_id':wizard.id,
			'type': 'ir.actions.act_window',
			'res_model': 'add.sketch.file',
			'view_id':view.id,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
			'context':{'glass_order_id':self.id}
		}
		
	
class GlassOrderLine(models.Model):
	_name="glass.order.line"
	_order="date_production,order_id,crystal_number"
	
	order_id = fields.Many2one('glass.order')
	product_id = fields.Many2one('product.product','Tipo Cristal')

	crystal_number = fields.Char('Nro. Cristal')
	calc_line_id = fields.Many2one('glass.sale.calculator.line',copy=False)
	base1 = fields.Integer("Base1 (L 4)",related="calc_line_id.base1",readonly=True)
	base2 = fields.Integer("Base2 (L 2)",related="calc_line_id.base2",readonly=True)
	altura1 = fields.Integer("Altura1 (L 1)",related="calc_line_id.height1",readonly=True)
	altura2 = fields.Integer("Altura2 (L 3)",related="calc_line_id.height1",readonly=True)

	area = fields.Float(u"Área M2",readonly=True,digits=(20,4))
	
	descuadre = fields.Char("Descuadre",size=7,related="calc_line_id.descuadre",readonly=True)
	polished_id = fields.Many2one(related="calc_line_id.polished_id",string="Pulido",readonly=True)
	entalle   = fields.Integer("Entalle",related="calc_line_id.entalle",readonly=True)
	plantilla = fields.Boolean("Plantilla",related="calc_line_id.template",readonly=True)
	page_number = fields.Integer(u"Nro. Pág.",related="calc_line_id.page_number",readonly=True)
	embalado = fields.Boolean("Embalado",related="calc_line_id.packed",readonly=True)
	image = fields.Binary("Embalado",related="calc_line_id.image",readonly=True)
	measures = fields.Char('Medidas',related='calc_line_id.measures',store=True)

	glass_break = fields.Boolean("Roto")
	glass_repo = fields.Boolean(u"Reposición")
	stock_move_ids = fields.Many2many('stock.move','glass_order_line_stock_move_rel','glass_order_line_id','stock_move_id',string='Stock Moves',copy=False)
	
	search_code = fields.Char(u'Código de búsqueda',related="lot_line_id.search_code")
	peso = fields.Float("Peso",digits=(20,4))
	lot_id = fields.Many2one('glass.lot','Lote')
	lot_line_id = fields.Many2one('glass.lot.line','Lote Linea')
	last_lot_line = fields.Many2one('glass.lot.line','Lote Linea')

	is_used = fields.Boolean('usado')
	image_page_number = fields.Char(u'Dirección')
	partner_id = fields.Many2one('res.partner', 'Cliente', related="order_id.partner_id",readonly=True)
	date_production = fields.Date('F. Produc.', related="order_id.date_production")
	state=fields.Selection([('process','En Proceso'),('ended','Producido'),('instock','Ingresado'),('send2partner','Entregado'),('cancelled','Anulado')],'Estado',default='process')
	image_page=fields.Binary('image pdf')
	retired_user = fields.Many2one('res.users',string='Retirado por')
	retired_date = fields.Date('Fecha de retiro')
	reference_order  =  fields.Char('Referencia OP', related='order_id.reference_order')
	in_packing_list = fields.Boolean('Packing List')

	#locacion temporal como auxiliar para agregar un location a locations
	location_tmp = fields.Many2one('custom.glass.location',string='Ubicacion') 
	# modelo a consultar
	locations =  fields.Many2many('custom.glass.location','glass_line_custom_location_rel','glass_line_id','custom_location_id',string='Ubicaciones')
	
	@api.multi
	def remove_line(self):
		if self.is_used or self.lot_line_id:
			raise UserError(u'No se puede retirar este cristal.\nEl cristal ya se encuentran en los lotes de producción.')
		self.write({
			'state':'cancelled',
			'retired_user':self.env.user.id,
			'retired_date':(datetime.now()-timedelta(hours=-5)).date(),
			'locations':False,
		})

	@api.multi
	def showimg(self):
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_glass_order_line_image' % module)
		data = {
			'name': _('Imagen'),
			'context': self._context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'glass.order.line',
			'view_id': view.id,
			'res_id':self.id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}
		return data

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.image_page_number and os.path.exists(rec.image_page_number):
				os.remove(rec.image_page_number)
		return super(GlassOrderLine,self).unlink()
