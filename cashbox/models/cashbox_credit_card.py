# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class CashboxCreditCardConfig(models.Model):
	_name = 'cashbox.credit.card.config'

	config_id = fields.Many2one('cashbox.config')
	analytic_tag_id = fields.Many2one('account.analytic.tag',required=True,string=u"Etiqueta analítica")
	card_type = fields.Selection([('debit',u'Débito'),('credit',u'Crédito')],required=True,default='debit')