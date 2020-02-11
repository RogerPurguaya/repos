# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,models,fields
from odoo.exceptions import UserError

from odoo.addons.account.wizard.pos_box import CashBox


# class PosBox(CashBox):
# 	_register = False

# 	@api.multi
# 	def run(self):
# 		active_model = self.env.context.get('active_model', False)
# 		active_ids = self.env.context.get('active_ids', [])

# 		if active_model == 'pos.session':
# 			bank_statements = [session.cash_register_id for session in self.env[active_model].browse(active_ids) if session.cash_register_id]
# 			if not bank_statements:
# 				raise UserError(_("There is no cash register for this PoS Session"))
# 			return self._run(bank_statements)
# 		else:
# 			return super(PosBox, self).run()


# class PosBoxIn(PosBox):
# 	_inherit = 'cash.box.in'

# 	def _calculate_values_for_statement_line(self, record):
# 		values = super(PosBoxIn, self)._calculate_values_for_statement_line(record=record)
# 		active_model = self.env.context.get('active_model', False)
# 		active_ids = self.env.context.get('active_ids', [])
# 		if active_model == 'pos.session' and active_ids:
# 			values['ref'] = self.env[active_model].browse(active_ids)[0].name
# 		return values

# sacar y poner dinero, sólo informativo
class CashboxMovementRecord(models.Model):
	_name = 'cashbox.movement.record'

	type_movement = fields.Selection([('in', 'Poner dinero'), ('out', 'Sacar dinero'),],string='Tipo de movimiento',required=True,readonly=True)
	user_id = fields.Many2one('res.users',u'Usuario responsable',required=True,readonly=True)
	journal_id = fields.Many2one('account.journal',u'Diario')
	session_id = fields.Many2one('cashbox.session',string=u'Sesión')
	amount = fields.Float('Monto')
	#reason = fields.Char('Motivo')

	_sql_constraints = [('amount_not_negative_or_zero','CHECK (amount > 0.0)',u'El monto debe debe mayor a cero (0.0)')]

	def register(self):
		if not self.session_id:
			raise UserError(u'No se ha establecido la sesión del movimiento')

	# def _calculate_values_for_statement_line(self, record):
	# 	values = super(PosBoxOut, self)._calculate_values_for_statement_line(record)
	# 	active_model = self.env.context.get('active_model', False)
	# 	active_ids = self.env.context.get('active_ids', [])
	# 	if active_model == 'pos.session' and active_ids:
	# 		values['ref'] = self.env[active_model].browse(active_ids)[0].name
	# 	return values
