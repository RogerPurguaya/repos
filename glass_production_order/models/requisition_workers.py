# -*- coding: utf-8 -*-
from odoo import api, fields, models,exceptions

# Materias primas: 
class RequisicionMaterialWorker(models.Model):
	_name = 'requisition.worker.material'
	requisition_id = fields.Many2one('glass.requisition',string='Req.')
	product_id = fields.Many2one('product.product',string='Producto')
	quantity = fields.Integer('Cantidad')
	process  = fields.Boolean('Procesado')
	
	@api.constrains('quantity')
	def _verify_quantity(self):
		for rec in self:
			if rec.quantity <= 0:
				raise exceptions.Warning(u'La cantidad ('+str(rec.quantity)+') ingresada no es valida\nIngrese una cantidad mayor a 0.')

	@api.multi
	def unlink(self):
		if self.process:
			raise exceptions.Warning('No es posible eliminar este requerimiento debido a que ya fue procesado.')
		return super(RequisicionMaterialWorker, self).unlink()
	
class RequisicionMaterialWorkerWizard(models.TransientModel):
	_name = 'requisition.worker.material.wizard'
	requisition_id = fields.Many2one('glass.requisition',string='Req.')
	lines_ids = fields.One2many('requisition.worker.wizard.line','material_id')

	@api.multi
	def add_items(self):
		lines = self.lines_ids.filtered(lambda x: x.quantity > 0)
		if len(lines) == 0:
			raise exceptions.Warning('No ha establecido cantidad para ningun producto o la cantidad ingresada es invalida')
		
		exist = lines.filtered(lambda x: x.product_id.id in self.requisition_id.raw_materials.filtered(lambda x:not x.process).mapped('product_id').ids)
		if len(exist) > 0:
			msg=''
			for line in exist:
				msg+='-> ' + line.product_id.name+'\n'
				line.quantity = 0
			raise exceptions.Warning('Los siguiente productos ya se encuentran en la lista de materias primas:\n'+msg)

		for item in lines:
			worker = self.env['requisition.worker.material'].create({
				'requisition_id':self.requisition_id.id,
				'product_id':item.product_id.id,
				'quantity':item.quantity,
			})
		return True

# Retazos:
class RequisicionScrapsWorker(models.Model):
	_name = 'requisition.worker.scraps'
	requisition_id = fields.Many2one('glass.requisition',string='Req.')
	product_id = fields.Many2one('product.product',string='Producto')
	quantity = fields.Integer('Cantidad')
	width = fields.Integer('Ancho') # para retazos
	height = fields.Integer('Alto') # para retazos
	process  = fields.Boolean('Procesado')

	@api.constrains('quantity')
	def _verify_quantity(self):
		for rec in self:
			if rec.quantity <= 0:
				raise exceptions.Warning(u'La cantidad ('+str(rec.quantity)+') ingresada no es valida\nIngrese una cantidad mayor a 0.')
	@api.multi
	def unlink(self):
		if self.process:
			raise exceptions.Warning('No es posible eliminar este requerimiento debido a que ya fue procesado.')
		return super(RequisicionScrapsWorker, self).unlink()


class RequisicionScrapsWorkerWizard(models.TransientModel):
	_name = 'requisition.worker.scraps.wizard'
	requisition_id = fields.Many2one('glass.requisition',string='Req.')
	lines_ids = fields.One2many('requisition.worker.wizard.line','scraps_id')

	@api.multi
	def add_items(self):
		lines = self.lines_ids.filtered(lambda x: x.quantity > 0)
		if len(lines) == 0:
			raise exceptions.Warning('No ha establecido cantidad para ningun producto o la cantidad ingresada es invalida')
		
		exist = lines.filtered(lambda x: x.product_id.id in self.requisition_id.scraps.filtered(lambda x:not x.process).mapped('product_id').ids)
		if len(exist) > 0:
			msg=''
			for line in exist:
				msg+='-> ' + line.product_id.name+'\n'
				line.quantity = 0
			raise exceptions.Warning('Los siguiente productos ya se encuentran en la lista de Retazos:\n'+msg)

		for item in lines:
			worker = self.env['requisition.worker.scraps'].create({
				'requisition_id':self.requisition_id.id,
				'product_id':item.product_id.id,
				'quantity':item.quantity,
				'width':item.width,
				'height':item.height,
			})
		return True

# Devolucion de Retazos:
class RequisicionWorkerScrapsReturn(models.Model):
	_name = 'requisition.worker.scraps.return'
	requisition_id = fields.Many2one('glass.requisition',string='Req.')
	product_id = fields.Many2one('product.product',string='Producto')
	quantity = fields.Integer('Cantidad')
	width = fields.Integer('Ancho') # para retazos
	height = fields.Integer('Alto') # para retazos
	process  = fields.Boolean('Procesado')

	@api.constrains('quantity')
	def _verify_quantity(self):
		for rec in self:
			if rec.quantity <= 0:
				raise exceptions.Warning(u'La cantidad ('+str(rec.quantity)+') ingresada no es valida\nIngrese una cantidad mayor a 0.')
	
	@api.constrains('width','height')
	def _verify_measures(self):
		for rec in self:
			if rec.width <= 0 or rec.height <= 0:
				raise exceptions.Warning(u'Las medidas ('+str(rec.width)+'X'+str(rec.height)+u') ingresadas no son válidas\nIngrese cantidades mayores a 0.')
			if rec.width > rec.height:
				raise exceptions.Warning(u'El ancho no puede ser menor al alto. Considere invertir las medidas')

	@api.multi
	def unlink(self):
		if self.process:
			raise exceptions.Warning('No es posible eliminar este requerimiento debido a que ya fue procesado.')
		return super(RequisicionWorkerScrapsReturn, self).unlink()


class RequisicionWorkerScrapsReturnWizard(models.TransientModel):
	_name = 'requisition.worker.scraps.return.wizard'
	requisition_id = fields.Many2one('glass.requisition',string='Req.')
	lines_ids = fields.One2many('requisition.worker.wizard.line','scraps_return_id')

	@api.multi
	def add_items(self):
		lines = self.lines_ids.filtered(lambda x: x.quantity > 0 and x.width > 0 and x.height > 0)
		if len(lines) == 0:
			raise exceptions.Warning('No ha establecido cantidad/ancho/alto para ningun producto o las cantidades ingresadas no son validas')
		
		exist = lines.filtered(lambda x: x.product_id.id in self.requisition_id.return_scraps.filtered(lambda x:not x.process).mapped('product_id').ids)
		if len(exist) > 0:
			msg=''
			for line in exist:
				msg+='-> ' + line.product_id.name+'\n'
				line.quantity = 0
			raise exceptions.Warning('Los siguiente productos ya se encuentran en la lista de Retazos a Devolver:\n'+msg)

		for item in lines:
			worker = self.env['requisition.worker.scraps.return'].create({
				'requisition_id':self.requisition_id.id,
				'product_id':item.product_id.id,
				'quantity':item.quantity,
				'width':item.width,
				'height':item.height,
			})
		return True

# modelo reutilizable para los 3 tipos de operacion (mat primas, retazos y dev. retazos)
class RequisicionWorkerWizardLine(models.TransientModel):
	_name = 'requisition.worker.wizard.line'
	material_id = fields.Many2one('requisition.worker.material.wizard')
	scraps_id = fields.Many2one('requisition.worker.scraps.wizard')
	scraps_return_id = fields.Many2one('requisition.worker.scraps.return.wizard')
	product_id = fields.Many2one('product.product',string='Producto')
	quantity = fields.Integer('Cantidad')
	width  = fields.Integer('Ancho') # para retazos
	height = fields.Integer('Alto') # para retazos
	available = fields.Integer('Disponible')

#class ProductTemplate(models.Model):
#	_inherit = 'product.template'
	#retazo = fields.Boolean('Es Retazo') # esto ya no se usa, remover

#class ProductProduct(models.Model):
	#_inherit = 'product.product'
	#retazo = fields.Boolean(related='product_tmpl_id.retazo') # esto ya no se usa, remover 

