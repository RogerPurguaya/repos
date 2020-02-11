# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class CashboxSummaryCash(models.Model):
	_name = 'cashbox.summary.cash'

	journal_id = fields.Many2one('account.journal',string='Diario',required=True)
	currency_id = fields.Many2one('res.currency',string='Moneda',compute='_get_currency',store=True)
	session_id = fields.Many2one('cashbox.session',string=u'Sesión') 
	reference = fields.Char('Referencia')
	balance_start = fields.Monetary(string='Balance Inicial',currency_field='currency_id',default=0.0)
	total_entry_encoding = fields.Monetary(string='Subtotal Transacciones',currency_field='currency_id',default=0.0)
	balance_end_real = fields.Monetary(string='Balance Final',currency_field='currency_id',default=0.0)
	difference = fields.Monetary(string='Diferencia',currency_field='currency_id',default=0.0)
	user_id = fields.Many2one('res.users',u'User')
	state = fields.Selection([('open','Nuevo'),('confirm','Validado')],default='open')

	@api.depends('journal_id')
	def _get_currency(self):
		for rec in self:
			j_currency = rec.journal_id.currency_id
			rec.currency_id = j_currency and j_currency.id or self.env.user.company_id.currency_id.id

	def _get_amount_in_session_currency(self,field_amount,type_exchange='sale'):
		self.ensure_one()
		amount = getattr(self,field_amount,None)
		if amount is None:
			raise UserError(u'Campo %s no válido'%field_amount)
		curr = self.currency_id
		# TODO controlar que sólo haya un tipo de cambio por moneda...
		exchange_type = self.session_id.exchange_type_ids.filtered(lambda e: e.currency_id==curr)
		if len(exchange_type)!=1:
			raise UserError(u'No ha establecido un tipo de cambio para la moneda %s o se ha encontrado más de uno para la misma.'%curr.name)
		rate = exchange_type.sale_rate if type_exchange == 'sale' else exchange_type.purchase_rate
		return curr.round(amount * rate)
		