# -*- coding: utf-8 -*-
from odoo import api, fields, models,exceptions
from datetime import datetime

class PurchaseRequisitionLine(models.Model):
	_inherit = 'purchase.requisition.line'

	description = fields.Char(u'Descripción')

class PurchaseRequisition(models.Model):
	_inherit = 'purchase.requisition'	
	
	sketch = fields.Binary('Croquis')
	file_name = fields.Char("Archivo")

class RequisitionMaterial(models.Model):
	_name = 'requisition.material'

	date = fields.Date(string='Fecha', default=datetime.now().date())
	config_id = fields.Many2one('glass.order.config',string='Config')
	product_id = fields.Many2one('product.product',string='Producto')
	materials_ids = fields.Many2many('product.product','req_material_product_rel','requisition_material_id','product_id')
	
	@api.constrains('product_id')
	def _verify_unique_product(self):
		for rec in self:
			exists = self.env['requisition.material'].search([('product_id','=',rec.product_id.id)])
			if len(exists) > 1:
				raise exceptions.Warning('Ya existe una Requisicion de Materiales para el producto: '+rec.product_id.name)

	@api.constrains('materials_ids')
	def _verify_materials_ids(self):
		for rec in self:
			bad = rec.materials_ids.filtered(lambda x: not x.uom_id.plancha)
			if any(bad):
				msg='\n'.join(bad.mapped(lambda x: '->'+x.name))
				raise exceptions.Warning('Los siguientes productos seleccionados no son de tipo plancha: \n'+msg)
	

