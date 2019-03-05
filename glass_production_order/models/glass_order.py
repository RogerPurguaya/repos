# -*- coding: utf-8 -*-

from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import time
from decimal import *
from pyPdf import PdfFileReader,PdfFileWriter
import base64
from StringIO import StringIO
import os
import sys
from subprocess import Popen, PIPE
import tempfile
from pdf2image import convert_from_path

class GlassOrder(models.Model):
	_name = 'glass.order'
	_inherit = ['mail.thread']
	_order = "id desc"

	name = fields.Char(u'Orden de producción',default='/')
	sale_order_id = fields.Many2one('sale.order', 'Pedido de venta',readonly=True)
	invoice_id = fields.Many2one('account.invoice','Documento',readonly=True,track_visibility='always')
	partner_id = fields.Many2one('res.partner', 'Cliente', related="sale_order_id.partner_id",readonly=True)
	delivery_department=fields.Char(u'Departamento', related="sale_order_id.partner_shipping_id.state_id.name")
	delivery_province=fields.Char(u'Provincia', related="sale_order_id.partner_shipping_id.province_id.name")
	delivery_street=fields.Char(u'Dirección Entrega', related="sale_order_id.partner_shipping_id.street")
	date_sale_order = fields.Datetime('Fecha de pedido de venta',related='sale_order_id.date_order')
	comercial_area=fields.Selection([('distribucion',u'Distribución'),('obra','Obra'),('proyecto','Proyecto')],u'Área Comercial' )
	obra =fields.Char('Obra')
	date_order = fields.Datetime('Fecha Emisión',default=datetime.now())
	date_production = fields.Date(u'Fecha de Producción')
	date_send = fields.Date(u'Fecha de Despacho')
	date_delivery = fields.Date(u'Fecha de Entrega')
	warehouse_id = fields.Many2one('stock.warehouse',u'Almacén Despacho',compute="getwarehouse")
	seller_id = fields.Many2one('res.users','Vendedor',related='sale_order_id.user_id')
	validated = fields.Boolean('Revisado')
	observ = fields.Text('Observaciones')
	state = fields.Selection([('draft','Generada'),
		('confirmed','Emitida'),
		('process','En Proceso'),
		('ended','Finalizada'),
		('delivered','Despachada')], 'Estado',default='draft',track_visibility='always')

	sale_lines = fields.One2many(related='sale_order_id.order_line')
	line_ids = fields.One2many('glass.order.line','order_id',u'Líneas a producir')
	# nuevo campo:
	#calc_proforma_lines_ids = fields.One2many('sale.calculadora.proforma.line','production_id','Calculadora Lines')
	total_area = fields.Float(u'Metros',compute="_gettotals",digits=(20,4))
	total_peso = fields.Float("Peso",compute="_gettotals",digits=(20,4))
	total_pzs = fields.Float("Total Pzs",compute="_gettotals")

	sketch = fields.Binary('Croquis')
	file2 = fields.Binary('aaaa')
	file_name = fields.Char("File Name")
	reference_order = fields.Char('Referencia OP')


	editable_croquis = fields.Boolean('editar croquis',default=True)


	invoice_count = fields.Integer(string='# of Invoices', related='sale_order_id.invoice_count', readonly=True)
	invoice_ids = fields.Many2many("account.invoice", string='Invoices', related="sale_order_id.invoice_ids", readonly=True)
	invoice_status = fields.Selection([
		('upselling', 'Upselling Opportunity'),
		('invoiced', 'Fully Invoiced'),
		('to invoice', 'To Invoice'),
		('no', 'Nothing to Invoice')
		], string='Invoice Status', related='sale_order_id.invoice_status', store=True, readonly=True)

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
		if self.state in ['draft','confirmed']:
			super(GlassOrder,self).unlink()
		else:
			raise UserError(u'No se puede eliminar una Orden de Producción en los estados: En proceso, FInalizada o Despachada')		

	@api.one
	def optimizar(self):
		self.state="process"
		return True

	@api.one
	def savecroquis(self):
		return True


	@api.one
	def save_pdf(self):
		self.editable_croquis=False
		return True		

	@api.multi
	def show_pdf(self):
		form_view_ref = self.env.ref('glass_production_order.view_glass_croquis_form', False)
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_glass_croquis_form' % module)
		data = {
			'name': _('Croquis'),
			'context': self._context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'glass.order',
			'view_id': view.id,
			'res_id':self.id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		} 
		return data


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
		form_view_ref = self.env.ref('glass_production_order.glass_remove_order_form_view', False)
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.glass_remove_order_form_view' % module)
		data = {
			'name': _('Remover Orden'),
			'context': self._context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'glass.remove.order',
			'view_id': view.id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		} 
		return data

	@api.one
	def getwarehouse(self):
		if self.sale_order_id:
			self.warehouse_id = self.sale_order_id.warehouse_id.id

	@api.one
	def _gettotals(self):
		ta =0
		tp =0
		n=0
		for line in self.line_ids:
			ta = ta+line.area
			tp=tp+line.peso
			n=n+1
		self.total_area=ta
		self.total_peso = tp
		self.total_pzs=n

	@api.one
	def validate_order(self):
		config_data = self.env['glass.order.config'].search([])
		if len(config_data)==0:
			raise UserError(u'No se encontraron los valores de configuración de producción')		
		config_data = self.env['glass.order.config'].search([])[0]
		
		for line in self.line_ids:
			line.unlink()
		tf = tempfile.NamedTemporaryFile()
		tf.close()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		f= open(tf.name, 'wb')
		f.write(base64.b64decode(self.sketch))
		f.close()
		pdf_path=tf.name		
		tdir = tempfile.mkdtemp()
		#print 'convitiendo las páginas'
		pages = convert_from_path(pdf_path, dpi=200,output_folder=tdir,fmt='jpg')
		#print 'fin convitiendo las páginas'
		lpages=[]
		n=0
		for page in pages:

			#print 'page-->',n
			n=n+1
			page.save(direccion+'image.jpg')
			with open(direccion+'image.jpg', "rb") as file:
				file_base64 = base64.b64encode(file.read())
				file.close()
			lpages.append(file_base64)
			#print "fin Proceso pages"
		for saleline in self.sale_lines:
			for calcline in saleline.id_type.id_line:
				if calcline.production_id.id ==self.id:
					cadnro = calcline.nro_cristal
					if cadnro:
						if ',' not in cadnro:
							acadnro = cadnro.split('-')
							if len(acadnro)>1:
								nini = int(acadnro[0])			
								nend = int(acadnro[1])+1
							else:
								nini = int(acadnro[0])
								nend = int(acadnro[0])+1
							#print nini,nend

							for x in range(nini,nend):
								area = float(0.00000)
								maxbase= calcline.base2
								maxaltura = calcline.altura2
								if calcline.base1>calcline.base2:
									maxbase= calcline.base1
								if calcline.altura1>calcline.altura2:
									maxaltura = calcline.altura1
								area= float(maxaltura*maxbase)/1000000
								peso = saleline.product_id.weight*area



								
								page_line =lpages[0]
								if calcline.page_number:
									if calcline.page_number!="":
										if len(lpages)<int(calcline.page_number)-1:
											raise UserError(u'El archivo PDF no contiene la página indicada')		
										page_line=lpages[int(calcline.page_number)-1]	


								vals ={
									'order_id':self.id,
									'product_id':saleline.product_id.id,
									'calc_line_id':calcline.id,
									'crystal_number':x,
									'area':area,
									'peso':peso,
									'image_page':page_line,
								}
								self.env['glass.order.line'].create(vals)
						else:
							acadnro = cadnro.split(',')
							if len(acadnro)>0:
								for a in acadnro:
									area = float(0.000000)
									maxbase= calcline.base2
									maxaltura = calcline.altura2
									if calcline.base1>calcline.base2:
										maxbase= calcline.base1
									if calcline.altura1>calcline.altura2:
										maxaltura = calcline.altura1
									area= float(maxaltura*maxbase)/1000000
									peso = saleline.product_id.weight*area



									

									if calcline.page_number:
										if calcline.page_number!="":
											pages = convert_from_path(pdf_path, 500,tdir,int(calcline.page_number),int(calcline.page_number),'png')
										else:
											pages = convert_from_path(pdf_path, 500,tdir,1,1,'png')
									else:
										pages = convert_from_path(pdf_path, 500,tdir,1,1,'png')
									pages[0].save(direccion+'image.png')

									file_base64 = ''
									with open(direccion+'image.png', "rb") as file:
										file_base64 = base64.b64encode(file.read())
										file.close()

									vals ={
										'order_id':self.id,
										'product_id':saleline.product_id.id,
										'calc_line_id':calcline.id,
										'crystal_number':a,
										'area':area,
										'peso':peso,
										'image_page':file_base64,
									}
									self.env['glass.order.line'].create(vals)
		self.state="confirmed"
		return True


class GlassOrderLine(models.Model):
	_name="glass.order.line"
	_order="date_production,order_id,crystal_number"
	
	order_id = fields.Many2one('glass.order')
	product_id = fields.Many2one('product.product','Tipo Cristal')
	calc_line_id= fields.Many2one('sale.calculadora.proforma.line')
	crystal_number = fields.Integer('Nro. Cristal')
	base1 = fields.Integer("Base1 (L 4)",related="calc_line_id.base1",readonly=True)
	base2 = fields.Integer("Base2 (L 2)",related="calc_line_id.base2",readonly=True)
	altura1 = fields.Integer("Altura1 (L 1)",related="calc_line_id.altura1",readonly=True)
	altura2 = fields.Integer("Altura2 (L 3)",related="calc_line_id.altura2",readonly=True)
	area = fields.Float("Área M2",compute="getarea",readonly=True,digits=(20,4))
	
	#Move_id campo que guarda el albaran de entrada al cual pertenece esta linea
	#move_id = fields.Many2one('stock.move', string='Move')
	#Campo que guarda el move de salida cuando esta linea es procesada para su salida de almacen
	#out_move = fields.Many2one('stock.move', string='Move Out')
	# Campo para guardar todos los movimientos que tenga esta order line:
	stock_move_ids = fields.Many2many('stock.move','glass_order_line_stock_move_rel','glass_order_line_id','stock_move_id',string='Stock Moves')
	descuadre = fields.Char("Descuadre",size=7,related="calc_line_id.descuadre",readonly=True)
	pulido1 = fields.Many2one("sale.pulido.proforma","Pulido",related="calc_line_id.pulido1",readonly=True)
	entalle = fields.Integer("Entalle",related="calc_line_id.entalle",readonly=True)
	plantilla = fields.Boolean("Plantilla",related="calc_line_id.plantilla",readonly=True)
	page_number = fields.Char(u"Nro. Pág.",related="calc_line_id.page_number",readonly=True)
	embalado = fields.Boolean("Embalado",related="calc_line_id.embalado",readonly=True)
	image = fields.Binary("Embalado",related="calc_line_id.image",readonly=True)
	glass_break=fields.Boolean("Roto")
	glass_repo=fields.Boolean("reposicioij")
	
	search_code = fields.Char(u'Código de búsqueda',related="lot_line_id.search_code")
	peso = fields.Float("Peso")
	lot_id = fields.Many2one('glass.lot','Lote')
	lot_line_id = fields.Many2one('glass.lot.line','Lote Linea')
	last_lot_line = fields.Many2one('glass.lot.line','Lote Linea')

	is_used = fields.Boolean('usado')

	partner_id = fields.Many2one('res.partner', 'Cliente', related="order_id.partner_id",readonly=True)
	date_production = fields.Date('F. Produc.', related="order_id.date_production")
	state=fields.Selection([('process','En Proceso'),('ended','Producido'),('instock','Ingresado'),('send2partner','Entregado')],'Estado',default='process')
	image_page=fields.Binary('image pdf')

	retired_user = fields.Many2one('res.users','Retirado por')
	retired_date = fields.Date('Fecha de retiro')
	reference_order  =  fields.Char('Referencia OP', related='order_id.reference_order')


	@api.one
	def getarea(self):
		self.area=Decimal(0.0000)
		l1 = Decimal(float(self.base1))
		if self.base2>self.base1:
			l1=Decimal(float(self.base2))
		l2 = Decimal(float(self.altura1))
		if self.altura2>self.altura1:
			l2=Decimal(float(self.altura2))
		self.area = round(float(float(l1)*float(l2))/float(1000000.0000),4)





	@api.multi
	def showimg(self):
		form_view_ref = self.env.ref('glass_production_order.view_glass_order_line_image', False)
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
	def return_wizard(self):
		#print self._context
		pass