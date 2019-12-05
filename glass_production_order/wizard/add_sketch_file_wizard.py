# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
import base64,os
from uuid import uuid1

class AddSketchFile(models.TransientModel):
	_name = 'add.sketch.file'
	sketch = fields.Binary(string='Croquis')
	file_name = fields.Char('')
	message = fields.Char('Message')
		
	@api.multi
	def preview(self):
		return  {"type": "ir.actions.do_nothing",}
	
	@api.multi
	def add_file(self):
		if not self.sketch:
			raise UserError('No ha seleccionado ningun archivo')
		try:
			conf = self.env['glass.order.config'].search([])[0]
		except IndexError as e:
			raise UserError(u'No se ha encontrado la configuracion para almacenar ficheros Pdf.')
		
		path = conf.path_glass_order_pdf
		order = self.env['sale.order'].browse(self._context['sale_order_id'])
		now = fields.Datetime.context_timestamp(self,datetime.now())
		name = 'order_%s_%s_%s.pdf'%(order.name,str(now)[:19].replace(':','_'),str(uuid1()))
		path += name
		with open(path,'wb') as file:
			file.write(base64.b64decode(self.sketch))
		self.env['glass.pdf.file'].create({
			'file_name':self.file_name,
			'pdf_name':self.file_name,
			'path_pdf':path,
			'sale_id':order.id,
		})
		return True

	# solo debería usarse desde glass.order form...
	def change_file(self):
		if not self.sketch:
			raise UserError(u'No ha seleccionado ningún archivo')
		try:
			conf = self.env['glass.order.config'].search([])[0]
		except IndexError as e:
			raise UserError(u'No se ha encontrado la configuración para almacenar ficheros Pdf.')

		path = conf.path_glass_order_pdf
		order = self.env['glass.order'].browse(self._context['glass_order_id'])
		now = fields.Datetime.context_timestamp(self,datetime.now())
		name = 'order_%s_%s_%s.pdf'%(order.name,str(now)[:19].replace(':','_'),str(uuid1()))
		path += name

		with open(path,'wb') as file:
			file.write(base64.b64decode(self.sketch))

		old_path = order.croquis_path
		order.write({'croquis_path':path})
		
		obj_pdf = self.env['glass.pdf.file'].search([('op_id','=',order.id)],limit=1)
		if obj_pdf:
			obj_pdf.write({'path_pdf':path})
		
		# limpiar el anterior:
		if old_path and os.path.exists(old_path):
			os.remove(old_path)
		else:
			print('Path file does not exist !')	
		return True