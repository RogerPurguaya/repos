# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta
from uuid import uuid1
import PyPDF2
from pyPdf import PdfFileReader,PdfFileWriter

class BuildGlassOrderWizard(models.TransientModel):
	_name='build.glass.order.wizard'

	sale_id = fields.Many2one('sale.order',string='Orden de venta',required=True)
	selected_file_id = fields.Many2one('glass.pdf.file',string='Archivo a incluir',domain=lambda self: self._context.get('file_domain',[]))
	file_name = fields.Char('Nombre del archivo',related="selected_file_id.pdf_name")
	destinity_order = fields.Selection([('local','En la ciudad'),('external','En otra ciudad')],u'Lugar de entrega',default="local")
	send2partner = fields.Boolean('Entregar en ubicacion del cliente',default=False)
	in_obra = fields.Boolean('Entregar en Obra')
	obra_text = fields.Char(u'Descripción de Obra')
	comercial_area=fields.Selection([('distribucion',u'Distribución'),('obra','Obra'),('proyecto','Proyecto')],u'Área Comercial',default="distribucion")
	
	def _get_config_default(self):
		config = self.env['glass.order.config'].search([],limit=1)
		if not config:
			raise UserError(u'No se encontraron los valores de configuración de producción')
		return config.id
	
	config_id = fields.Many2one('glass.order.config',string='Config',default=_get_config_default)

	def create_production_order(self):
		"""Método para crear una Órden de producción, éste debería ser la única forma de crear 
		una órden de producción, ya que valida todo lo necesario"""
		self.ensure_one()
		
		# if len(self.invoice_ids.filtered(lambda x: x.state!='cancel'))==0:
		# 	raise UserError(u"No se puede generar OP cuando no se tiene una factura vigente")
		
		# validando restricciones de terminos de pago:
		# if self.payment_term_id:
		# 	configs=self.env['config.payment.term'].search([('operation','=','generate_op')])
		# 	if len(configs) == 1: # solo puede estar en una conf
		# 		if self.payment_term_id.id in configs[0].payment_term_ids.ids:
		# 			invoice = self.invoice_ids[0]
		# 			payed = invoice.amount_total - invoice.residual
		# 			percentage = (float(payed)/float(invoice.amount_total)) * 100
		# 			if percentage < configs[0].minimal:
		# 				raise exceptions.Warning(u'No puede emitirse la Orden de Producción\nEl porcentaje mínimo para el plazo de pago elegido es del '+str(configs[0].minimal)+' %.')
		# 	else:
		# 		raise exceptions.Warning('No ha configurado las condiciones para el Plazo de pago al generar OP')

		order_old =  None  #O P devuelta
		config = self.config_id
		gen_orders = self.sale_id.op_ids # sale op's
		if gen_orders and not self.sale_id.before_invoice:
			raise UserError(u"El pedido %s ya tiene órdenes de producción asignadas"%self.sale_id.name)
		pendings = self.sale_id.op_returned_ids.filtered(lambda x: not x.corrected)
		if pendings:
			order_old = pendings[0] # Se subsana la primera de las órdenes devueltas 
			order_name = order_old.name[4:] # excluir el 'DEV-' (una orden devuelta tiene el prefijo DEV-)
		else:
			order_name = self.sale_id.name
			nextnumber = len(gen_orders)
			if nextnumber>0:
				order_name = '%s.%d'%(order_name,nextnumber)
		if order_old: order_old.corrected=True

		lines_vals = self._get_glass_line_vals(order_name)
		order_vals = self._prepare_glass_order_vals(lines_vals,order_name)
		neworder = self.env['glass.order'].create(order_vals)
		# bloquear entrega manual de albaranes
		neworder.line_ids.mapped('calc_line_id').with_context(force_write=True).write({
			'glass_order_id':neworder.id,
			})

		pickings = self.sale_id.mapped('picking_ids')
		pickings.write({'sale_picking':True})
		self.selected_file_id.write({
			'is_editable':False,
			'is_used':True,
			'op_id':neworder.id,
		})
		module = __name__.split('addons.')[1].split('.')[0]
		return {
			'name':neworder.name,
			'res_id':neworder.id,
			'type': 'ir.actions.act_window',
			'res_model': neworder._name,
			'view_id': self.env.ref('%s.view_glass_order_form'%module).id,
			'view_mode': 'form',
			'view_type': 'form',
			}
		
	def _prepare_glass_order_vals(self,glass_line_vals,order_name):
		## make O.P. name
		# param: glass_line_vals = [{values},{values},...]
		# param: order_name = name of order
		lim_templado =  self.config_id.limit_ids.filtered(lambda x: x.motive_limit=='templado')
		if not lim_templado:
			raise UserError(u"No se ha encontrado la configuración de plazos de producción para templados.")
		if len(lim_templado)>1:
			raise UserError(u"Se ha encontrado más de una configuración de plazos de producción para templados.")
		if not any(glass_line_vals):
			raise UserError(u"No se han encontrado líneas de calculadora pendientes de Órden de Producción.")

		area = sum(map(lambda l: l['area'],glass_line_vals))
		calc_lines = self.env['glass.sale.calculator.line'].browse(map(lambda x: x['calc_line_id'],glass_line_vals))
		with_entalle = calc_lines.filtered(lambda x: x.entalle>0 or x.descuadre)
		
		days_prod = days_send = 0 # days for production

		if area<51: days_prod = lim_templado.zero_2_50
		if area<101 and area>50: days_prod = lim_templado.fiftyone_2_100
		if area<201 and area>101: days_prod = lim_templado.onehundred1_2_200
		if area>200: days_prod = lim_templado.more_2_200
		if self.in_obra: days_prod = days_prod+lim_templado.obras	
		if with_entalle: days_prod = days_prod+lim_templado.entalle
		
		dateprod = datetime.now().date()+timedelta(days=days_prod)
		if dateprod.weekday()==6: dateprod = dateprod+timedelta(days=1)

		aux = False # auxiliar??
		if self.destinity_order=='local':
			days_send = days_send+lim_templado.local_send
			aux = True
		if self.destinity_order=='external':
			days_send = days_send+lim_templado.external_send	
		datesend = dateprod+timedelta(days=days_send)
		if self.send2partner:
			days_send = days_send+lim_templado.send2partner				

		# si la entrega es en la ciudad, delivery_date es igual a la send_date
		datedeli = datesend if aux else datesend+timedelta(days=days_send)
		return {
			'sale_order_id':self.sale_id.id,
			'name':order_name,
			'date_production':dateprod,
			'date_send':datesend,
			'date_delivery':datedeli,
			'file_name':self.file_name,
			'obra':self.obra_text,
			'destinity_order':self.destinity_order,
			'send2partner':self.send2partner,
			'in_obra':self.in_obra,
			'croquis_path':self.selected_file_id.path_pdf,
			'comercial_area':self.comercial_area,
			'reference_order': self.sale_id.reference_order or '',
			'state':'confirmed',
			'line_ids':[(0,0,values) for values in glass_line_vals]
		}

	def _get_glass_line_vals(self,order_name):
		# ruta donde se almacenan los pdf de cada glass order line:
		path_lines = self.config_id.path_glass_lines_pdf
		try:
			file = open(self.selected_file_id.path_pdf,"rb")
			opened_pdf = PyPDF2.PdfFileReader(file)
		except IOError as e:
			raise UserError(u'¡Archivo PDF removido,no encontrado o sin permisos de acceso!')

		items,dict_paths = [],{}

		for o_line in self.sale_id.order_line.filtered('calculator_id'):
			to_produce_lines = o_line.calculator_id._get_lines_to_produce()
			for p_line in to_produce_lines: 
				p_number = p_line.page_number
				if p_number and p_number not in dict_paths.keys(): # all should have page_number???
					try:
						# build pdf page from op pdf file
						output = PyPDF2.PdfFileWriter()
						output.addPage(opened_pdf.getPage(p_number-1))
						# name format = op_name + page_num + uuid() code
						pdf_name = '%s_%d_%s.pdf'%(order_name,p_number,str(uuid1()))
						pdf_path = path_lines+pdf_name
						with open(pdf_path,"wb") as output_pdf:
							output.write(output_pdf)
						dict_paths[p_number] = pdf_path
					except IOError as e:
						raise UserError(u'¡Archivo PDF para generar OP no encontrado!')
					except Exception:
						raise UserError(u'Ocurrió un error al generar los ficheros PDF, es posible que no haya asignado correctamente los números de página en su(s) calculadora(s)')
					finally:
						file.close()
				area = p_line.area/p_line.quantity
				product = p_line.calculator_id.product_id
				weight = product.weight*area
				for num in p_line.get_crystal_numbers():
					items.append(self._prepare_glass_line_vals({
						'product_id':product.id, # cristales comunes
						'calc_line_id':p_line.id,
						'crystal_number':str(num),
						'area':area,
						'peso':weight,
						'image_page_number':dict_paths.get(p_number,False),
					}))
		return items

	def _prepare_glass_line_vals(self,dict_vals):
		"""Destinado a herencia"""
		return dict_vals
