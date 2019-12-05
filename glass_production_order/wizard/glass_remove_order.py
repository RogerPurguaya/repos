# -*- encoding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime
import codecs

class GlassRemoveOrder(models.TransientModel):
	_name = 'glass.remove.order'

	date_remove = fields.Date('Fecha',default=datetime.now().date())
	motive_remove = fields.Text('Motivo')
	order_name = fields.Char(string='Orden de Producción')
		
	def remove_order(self):
		order = self.env['glass.order'].browse(self._context.get('order_id'))
		used_lines = order.line_ids.filtered(lambda x: x.is_used or x.lot_line_id)
		if any(used_lines):
			raise UserError(u'No se puede retirar la OP.\nUno o varios elementos de esta orden de producción ya se encuentran en los lotes de producción.')		

		# si no es factura adelantada:
		sale_order = order.sale_order_id
		if not sale_order.before_invoice:
			invoices = sale_order.invoice_ids
			inv_payed = invoices.filtered(lambda x: x.state=='paid')
			if inv_payed:
				msg = '\n'.join(inv_payed.mapped(lambda x: '- '+x.number))
				raise UserError(u'La siguientes facturas ya se encuentran en estado pagado:\n%s\nEs necesario anular los pagos asociados para devolver esta O.P.'%msg)
			invoices.filtered(lambda x: x.state in ('draft','proforma','open')).action_invoice_cancel()
			sale_order.action_cancel()
			sale_order.action_draft() 
		
		order.line_ids.mapped('calc_line_id').with_context(force_write=True).write({'glass_order_id':False})
		order.line_ids.unlink()
		pdf_files = self.env['glass.pdf.file'].search([('op_id','=',order.id)])
		pdf_files.write({'is_used':False,'is_editable':True})
		order.write({'state':'returned','name':'DEV-'+order.name})
		
		msg = u'El usuario %s ha retirado la Orden de Producción: %s'%(self.env.user.name,order.name)
		
		if self.motive_remove:
			msg += u' por el motivo: "%s"'%self.motive_remove.strip()
		if self.date_remove:
			msg += ', asignando la fecha: %s.'%str(self.date_remove)
		# sender = self.env['send.email.event'].create({
		# 	'subject': u'Retiro de Orden de Producción: '+order.name,
		# 	'message': msg,
		# })
		# res = sender.send_emails(motive='op_returned') 
		#return res



