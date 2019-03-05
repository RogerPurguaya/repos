# -*- coding: utf-8 -*-

from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime
from pyPdf import PdfFileReader,PdfFileWriter
import base64
from StringIO import StringIO
import os
import sys
from subprocess import Popen, PIPE
import tempfile
from pdf2image import convert_from_path
from PIL import Image


class GlassProductionControlWizard(models.Model):
	_name='glass.productioncontrol.wizard'

	stage = fields.Selection([('corte','Corte'),('pulido','Pulido'),('entalle','Entalle'),('lavado','Lavado')],'Etapa')
	search_code = fields.Char('Producto')
	lot_line_id = fields.Many2one('glass.lot.line',u'Línea de lote')
	production_order = fields.Many2one('glass.order','OP')
	partner_id = fields.Many2one('res.partner',string='Cliente')
	product_id = fields.Many2one('product.product',string='Cristal')
	lot_id = fields.Many2one('glass.lot')
	obra = fields.Char(string='Obra')

	image_glass = fields.Binary("imagen")
	image_page = fields.Binary("Page")
	image_page_r90 = fields.Binary("Page")
	image_page_r180 = fields.Binary("Page")
	image_page_r270 = fields.Binary("Page")
	sketch = fields.Binary("Croquis")
	nro_cristal = fields.Char("Nro. Cristal",related="lot_line_id.nro_cristal")
	is_used = fields.Boolean('usado',default=False)
	existe = fields.Integer('existe')
	messageline= fields.Char('Mensaje',default='El elemento ya fue registrado en esta etapa')
	rotate = fields.Boolean('Rotar', default=False)

	@api.one
	def setrotate(self):
		self.rotate= not self.rotate


	@api.model
	def default_get(self,fields):
		res =super(GlassProductionControlWizard,self).default_get(fields)
		config_data = self.env['glass.order.config'].search([])
		if len(config_data)==0:
			raise UserError(u'No se encontraron los valores de configuración de producción')		
		config_data = self.env['glass.order.config'].search([])[0]
		ustage = False
		for userstage in config_data.userstage:
			if userstage.user_id.id == self.env.user.id:
				ustage=userstage
		if ustage:
			res.update({'stage':ustage.stage})
		else:
			raise UserError(u'El usuario actual no tiene permisos para acceder a esta funcionalidad')		
		return res



	@api.multi
	@api.onchange('search_code')
	def onchangecode(self):
		self.ensure_one()
		vals={}

		if self.search_code:
			config_data = self.env['glass.order.config'].search([])
			if len(config_data)==0:
				raise UserError(u'No se encontraron los valores de configuración de producción')		
			config_data = self.env['glass.order.config'].search([])[0]
			existe = self.env['glass.lot.line'].search([('search_code','=',self.search_code)])

			if len(existe)>0:
				lsttmp=[]
				page_one=False
				existe_act = existe[0]
				self.is_used=False
				self.lot_line_id=False
				self.production_order=False
				self.partner_id=False
				self.product_id=False
				self.lot_id=False
				self.obra=False
				self.image_glass=False
				self.sketch=False
				self.search_code=False

				vals={}
				# if existe_act.entalle==False
				# if existe_act.order_prod_id.sketch:
				# 	value = existe_act.order_prod_id.sketch.decode('base64')
				# 	f = StringIO(value)	
				# 	tf = tempfile.NamedTemporaryFile()
				# 	tf.close()

				# 	direccion = self.env['main.parameter'].search([])[0].dir_create_file
				# 	f= open(tf.name, 'wb')
				# 	f.write(base64.b64decode(existe_act.order_prod_id.sketch))
				# 	f.close()
					
				# 	pdf_path=tf.name		
				# 	tdir = tempfile.mkdtemp()
				# 	if existe_act.page_number:
				# 		if existe_act.page_number!="":
				# 			pages = convert_from_path(pdf_path, 500,tdir,int(existe_act.page_number),int(existe_act.page_number),'png')
				# 		else:
				# 			pages = convert_from_path(pdf_path, 500,tdir,1,1,'png')
				# 	else:
				# 		pages = convert_from_path(pdf_path, 500,tdir,1,1,'png')
				# 	pages[0].save(direccion+'image.png')
				# 	lsttmp = os.listdir(tdir)

				# 	file_base64 = ''
				# 	with open(direccion+'image.png', "rb") as file:
				# 		file_base64 = base64.b64encode(file.read())
				# 		file.close()
				direccion = self.env['main.parameter'].search([])[0].dir_create_file
				self.image_page = existe_act.order_line_id.image_page
				with open(direccion+'image_r.jpg','wb+') as f:
					f.write(base64.b64decode(existe_act.order_line_id.image_page))
					f.close()
				im = Image.open(direccion+'image_r.jpg')		
				im.rotate(90).save(direccion+'image_r90.jpg',"JPEG")
				im1 = Image.open(direccion+'image_r.jpg')
				im1.rotate(180).save(direccion+'image_r180.jpg',"JPEG")
				im2 = Image.open(direccion+'image_r.jpg')
				im2.rotate(270).save(direccion+'image_r270.jpg',"JPEG")

				f= open(direccion+'image_r90.jpg',"rb")
				file_base6490=base64.b64encode(f.read())
				f.close()
				
				f= open(direccion+'image_r180.jpg',"rb")
				file_base64180=base64.b64encode(f.read())
				f.close()

				f= open(direccion+'image_r270.jpg',"rb")
				file_base64270=base64.b64encode(f.read())
				f.close()




				
				self.image_page_r90 = file_base6490
				self.image_page_r180 = file_base64180
				self.image_page_r270 = file_base64270
				vals['image_page']=existe_act.order_line_id.image_page

					# os.remove(tdir)
					

				
				vals.update({
					'lot_line_id':existe_act.id,
					'production_order':existe_act.order_prod_id.id,
					'partner_id':existe_act.order_prod_id.partner_id.id,
					'product_id':existe_act.product_id.id,
					'lot_id':existe_act.lot_id.id,
					'obra':existe_act.order_prod_id.obra,
					'image_glass':existe_act.image_glass,
					'nro_cristal':existe_act.nro_cristal,
					'sketch':existe_act.order_prod_id.sketch,
					'image_page_r90':file_base6490,
					'image_page_r180': file_base64180,
					'image_page_r270': file_base64270,


				})
				self.lot_line_id=existe_act.id
				self.production_order=existe_act.order_prod_id.id
				self.partner_id=existe_act.order_prod_id.partner_id.id
				self.product_id=existe_act.product_id.id
				self.lot_id=existe_act.lot_id.id
				self.obra=existe_act.order_prod_id.obra
				self.image_glass=existe_act.image_glass
				self.nro_cristal=existe_act.nro_cristal

				self.sketch=existe_act.order_prod_id.sketch
				self.messageline=''
				stage_obj = self.env['glass.stage.record']
				#print self.stage
				#print self.lot_line_id.calc_line_id.entalle
				
				if self.stage=='entalle':
					if self.lot_line_id.calc_line_id.entalle==0:
						self.messageline='El cristal no tiene etapa de entalle'
						vals.update({'messageline':'El cristal no tiene etapa de entalle'})
						self.search_code=''
						self.is_used=True
						self.write(vals)
						return {'value':vals}		
				ext = stage_obj.search([('stage','=',self.stage),('lot_line_id','=',existe_act.id)])
				if len(ext)==0:
					self.save_stage()
				else:
					self.messageline='El cristal ya fue procesado en esta etapa'
					vals.update({'messageline':'El cristal ya fue procesado en esta etapa'})
					self.is_used=True
				

			else:
				self.is_used=False
				self.lot_line_id=False
				self.production_order=False
				self.partner_id=False
				self.product_id=False
				self.lot_id=False
				self.obra=False
				self.image_glass=False
				self.sketch=False
				self.search_code=False

				self.image_page=False

				
		self.search_code=''
		self.write(vals)
		
		return {'value':vals}

	@api.one
	def save_stage(self):
		stage_obj = self.env['glass.stage.record']
		if self.lot_line_id:
			existe = self.env['glass.lot.line'].search([('search_code','=',self.search_code)])
			if len(existe)>0:
				existe_act = existe[0]
				ext = stage_obj.search([('stage','=',self.stage),('lot_line_id','=',existe_act.id)])
				# si ya se registró solo se muestran los valores pero no se registra nuevamente
				if len(ext)>0:
					self.is_used=True
					self.lot_line_id=existe_act.id
					return
					# raise UserError(u'El cristal seleccionado ya fue registrado en la etapa seleccionada')		
				self.lot_line_id=existe_act.id
			#print 1
			if self.lot_line_id:
				#print 2
				if self.stage=='lavado':
					#print 3
				
					if self.lot_line_id.calc_line_id.entalle:
						#print 4,self.lot_line_id.calc_line_id.entalle
						pasoentalle = stage_obj.search([('stage','=','entalle'),('lot_line_id','=',self.lot_line_id.id)])
						if len(pasoentalle)==0:
							self.is_used=True
							self.lot_line_id=False
							self.production_order=False
							self.partner_id=False
							self.product_id=False
							self.lot_id=False
							self.obra=False
							self.image_glass=False
							self.sketch=False
							self.search_code=False
							return
							# raise UserError(u'No se puede registrar LAVADO si no se ha pasado por ENTALLE')		
				data = {
						'user_id':self.env.uid,
						'date':datetime.now(),
						'time':datetime.now().time(),
						'stage':self.stage,
						'lot_line_id':self.lot_line_id.id,
					}

				stage_obj.create(data)
				if self.stage == 'corte':
					self.lot_line_id.write({'corte':True})
					self.lot_line_id.corte = True
				if self.stage == 'pulido':
					self.lot_line_id.write({'pulido':True})
					self.lot_line_id.pulido = True
				if self.stage == 'entalle':
					self.lot_line_id.write({'entalle':True})
					self.lot_line_id.entalle = True
				if self.stage == 'lavado':
					self.lot_line_id.write({'lavado':True})
					self.lot_line_id.lavado = True

		return True