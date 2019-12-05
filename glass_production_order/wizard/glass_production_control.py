# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta
from pyPdf import PdfFileWriter
import PyPDF2

class GlassProductionControlWizard(models.TransientModel):
	_name='glass.productioncontrol.wizard'
	stage = fields.Selection([('corte','Corte'),('pulido','Pulido'),('entalle','Entalle'),('lavado','Lavado')],'Etapa')
	search_code = fields.Char('Producto')
	production_order = fields.Many2one('glass.order','OP')
	image_glass = fields.Binary("imagen")
	nro_cristal = fields.Char("Nro. Cristal")
	messageline= fields.Char('Mensaje')
	path = fields.Char('Path File')

	@api.multi
	def get_new_element(self):
		path = self.env['main.parameter'].search([])[0].download_directory
		path += 'previsualizacion_op.pdf'
		writer = PyPDF2.PdfFileWriter()
		writer.insertBlankPage(width=500, height=500, index=0)
		with open(path, "wb") as outputStream: 
			writer.write(outputStream) #write pages to new PDF
		wizard = self.create({'path':path})
		return {
			'name':'Control de Produccion',
			'res_id':wizard.id,
			'type': 'ir.actions.act_window',
			'res_model': 'glass.productioncontrol.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}

	@api.model
	def default_get(self,fields):
		res =super(GlassProductionControlWizard,self).default_get(fields)
		conf = self.env['glass.order.config'].search([])
		if len(conf)==0:
			raise UserError(u'No se encontraron los valores de configuración de producción')	
		conf = self.env['glass.order.config'].search([])[0]
		ustage = False
		for userstage in conf.userstage:
			if userstage.user_id.id == self.env.user.id:
				ustage=userstage
		if ustage:
			res.update({'stage':ustage.stage})
		else:
			raise UserError(u'El usuario actual no tiene permisos para acceder a esta funcionalidad')		
		return res

	@api.onchange('search_code')
	def onchangecode(self):
		self.ensure_one()
		this  = self.browse(self._origin.id)
		res   = {}
		code  = self.search_code or 'undefined'
		stage = self.stage
		line = self.env['glass.lot.line'].search([('search_code','=',code)])
		if len(line)==1:
			self.messageline = self.search_code = ''
			if stage in ['lavado','entalle']:
				if stage=='entalle' and line.calc_line_id.entalle==0:
					res = {'production_order':False,'nro_cristal':False,'messageline':'El cristal no tiene etapa de entalle'}
					return {'value':res}
				res = self.save_stage(stage,line)[0]
				try:
					file = open(line.order_line_id.image_page_number,'rb')
					content = file.read()
					file_new = open(this.path,'wb')
					file_new.write(content)
					file.close()
					file_new.close()
				except TypeError as e:
					writer = PyPDF2.PdfFileWriter()
					writer.insertBlankPage(width=500, height=500, index=0)
					with open(this.path, "wb") as outputStream: 
						writer.write(outputStream) #write pages to new PDF
				except IOError as e:
					writer = PyPDF2.PdfFileWriter()
					writer.insertBlankPage(width=500, height=500, index=0)
					with open(this.path, "wb") as outputStream: 
						writer.write(outputStream) #write pages to new PDF
			elif stage in ['corte','pulido']:
				res = self.save_stage(stage,line)[0]
				res.update({'image_glass':line.image_glass})
		else:
			msg = u'Código no encontrado!' if self.search_code else ''
			self.search_code = ''
			res = {'production_order':False,'nro_cristal':False,'image_glass':False,'messageline':msg}
			if stage in ['lavado','entalle']:
				writer = PyPDF2.PdfFileWriter()
				writer.insertBlankPage(width=500, height=500, index=0)
				with open(this.path, "wb") as outputStream: 
					writer.write(outputStream)
		return {'value':res}

	@api.one
	def save_stage(self,stage,line):
		if line[stage]:
			return {
				'production_order':False,
				'nro_cristal':False,
				'image_glass':False,
				'messageline':'El cristal ya fue procesado en la etapa :'+stage.upper(),
				}
		self.env['glass.stage.record'].create({
			'user_id':self.env.uid,
			'date':(datetime.now()-timedelta(hours=5)).date(),
			'time':(datetime.now()-timedelta(hours=5)).time(),
			'stage':stage,
			'lot_line_id':line.id,
		})
		line.write({stage:True})
		return {
				'production_order':line.order_prod_id.id,
				'nro_cristal':line.nro_cristal,
				'messageline':''
				}