# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class CashboxCashControlWizard(models.TransientModel):
	_name = 'cashbox.cash.control.wizard'

	@api.depends('journal_id')
	def _get_currency(self):
		for rec in self:
			j_currency = rec.journal_id.currency_id
			rec.currency_id = j_currency and j_currency.id or self.env.user.company_id.currency_id.id

	session_id = fields.Many2one('cashbox.session',string=u'Sesión')
	journal_id = fields.Many2one('account.journal',domain=lambda self: self._context.get('dom_journals',[]))
	currency_id = fields.Many2one('res.currency',u'Moneda',compute='_get_currency')
	line_ids = fields.One2many('cashbox.cash.control.wizard.line','cash_control_id',string='Detalle')

	def process(self):
		total = sum(self.line_ids.mapped('subtotal'))
		if total == 0.0:
			raise UserError(u'El monto debe ser mayor a cero.')
		line = self.session_id.summary_cash_ids.filtered(lambda line: line.journal_id==self.journal_id)
		field_amount = self._context.get('balance')
		field_amount = 'balance_start' if field_amount=='start' else 'balance_end_real'
		line.write({field_amount:total})
		return True

class CashboxCashControlWizardLine(models.TransientModel):
	
	_name = 'cashbox.cash.control.wizard.line'

	@api.depends('coin_value', 'number')
	def _sub_total(self):
		""" Calculates Sub total"""
		for rec in self:
			rec.subtotal = rec.coin_value * rec.number
	
	cash_control_id = fields.Many2one('cashbox.cash.control.wizard')
	coin_value = fields.Selection(string=u'Denominación', selection=[
		(200, '200'),
		(100, '100'),
		(50 , '50'),
		(20 , '20'),
		(10 , '10'),
		(5  , '5'),
		(2  , '2'),
		(1  , '1'),],required=True)
	
	number = fields.Integer(string='Nro de ítems')
	subtotal = fields.Float(compute='_sub_total', string='Subtotal', digits=0, readonly=True)

	#cashbox_id = fields.Many2one('account.bank.statement.cashbox', string="Cashbox")