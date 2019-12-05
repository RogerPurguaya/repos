# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions
from datetime import datetime,timedelta
class GlassScrap(models.Model):
	_name = 'glass.scrap.move'
	product_id = fields.Many2one('product.product',required=True)
	width = fields.Integer('Ancho',required=True)
	height = fields.Integer('Alto',required=True)
	quantity = fields.Integer('Cantidad')
	location = fields.Many2one('stock.location')
	record_ids = fields.One2many('glass.scrap.record','scrap_move_id')
	name = fields.Char('Nombre',compute='_get_name',store=True)

	@api.depends('width','height')
	def _get_name(self):
		for rec in self:
			dim = [rec.width,rec.height]
			rec.name = str(min(dim))+'x'+str(max(dim))+'mm'
	
	@api.model
	def create(self, values):
		exist = self.search([('product_id','=',values['product_id']),('width','=',values['width']),('height','=',values['height'])])
		if any(exist):
			raise exceptions.Warning('Ya existe un registro con el producto y dimensiones ingresadas')
		return super(GlassScrap, self).create(values)

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.quantity != 0:
				raise exceptions.Warning(u'No es posible eliminar un registro con saldo distinto a cero')
		return super(GlassScrap, self).unlink()
	

class GlassScrapRecord(models.Model):
	_name = 'glass.scrap.record'
	move_id = fields.Many2one('stock.move')
	product_id = fields.Many2one('product.product')
	date = fields.Date('Fecha',default=(datetime.now()-timedelta(hours=5)).date())
	user_id = fields.Many2one('res.users')
	area = fields.Float('Area')
	pieces = fields.Integer('Piezas')
	scrap_move_id = fields.Many2one('glass.scrap.move')
	type_move = fields.Selection([('in','In'),('out','Out')])