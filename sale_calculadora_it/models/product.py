# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError

class ProductCategory(models.Model):
	_inherit = 'product.category'

	min_sale=fields.Float(u'Mínimo Vendible')
	uom_min_sale=fields.Many2one('product.uom',u'Unidad')

class ProductProduct(models.Model):
	_inherit='product.template'
	allow_metric_sale = fields.Boolean('Permite Venta metro lineal')

class ProductProduct(models.Model):
	_inherit='product.product'
	allow_metric_sale = fields.Boolean(related='product_tmpl_id.allow_metric_sale')

		
