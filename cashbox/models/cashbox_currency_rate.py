# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class CashboxExchangeType(models.Model):
	_name = 'cashbox.exchange.type'
	_description = u'Tipo de cambio comercial para Caja'
	
	date = fields.Date('Fecha',default=lambda self:fields.Date.context_today(self))
	currency_id = fields.Many2one('res.currency',string='Moneda',required=True)
	type_sale = fields.Float('Tipo de venta',required=True)
	type_purchase = fields.Float('Tipo de compra',required=True)
	sale_rate = fields.Float('Sale rate',compute='_compute_rate',store=True)
	purchase_rate = fields.Float('Purchase rate',compute='_compute_rate',store=True)

	_sql_constraints = [
		('positive_exchanges','CHECK (type_sale > 0.0 AND type_purchase > 0.0)',u'Los tipos de cambio no pueden ser negativos.'),
		('unique_date','UNIQUE (date)',u'La fecha debe ser única por registro')]
	
	@api.depends('type_sale','type_purchase')
	def _compute_rate(self):
		for rec in self:
			rec.sale_rate = 1.0/rec.type_sale
			rec.purchase_rate = 1.0/rec.type_purchase

	@api.multi
	@api.depends('date','currency_id.name','type_sale')
	def name_get(self):
		result = []
		for rate in self:
			name = '%s - %s (%.3f)'%(rate.date,rate.currency_id.name,rate.type_sale)
			result.append((rate.id, name))
		return result