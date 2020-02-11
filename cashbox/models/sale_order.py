# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import json
from datetime import datetime

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	@api.model
	def get_available_so_pos(self,partner_id=False):
		"""Retornar sólo SO en estado 'sale' y sin facturas vigentes"""
		domain = [('state','=','sale')]
		SaleOrder = self.env['sale.order']
		if partner_id:
			domain.append(('partner_id','=',partner_id))
		orders = SaleOrder.search(domain)
		# FIXME Filtar ordenes sin facturas canceladas, debería 
		# poder generar una factura direc.desde la S.O.?
		for order in orders:
			if order.invoice_ids.filtered(lambda i: i.state!='cancel'): continue
			SaleOrder |= order
		return [{'id':o.id,'name':o.name,'date_order':o.date_order,'partner_id':(o.partner_id.id,o.partner_id.name,)} for o in SaleOrder]

	@api.model
	def create_and_validate_invoice(self,pos_order,order_id):
		order = self.browse(order_id)
		if order.state != 'sale':
			return {
				'title': u'Orden de venta inválida',
				'status':'warning',
				'refund': {
					'id': order.id,
					'name': order.name,
				}
			}
		wiz = self.env['sale.advance.payment.inv'].sudo().with_context(active_ids=[order.id]).create({
			'advance_payment_method':'all',
		})
		err = None
		#try:
		wiz.create_invoices()
		# FIXME Por ahora según el tipo de partner...
		ebill_res = {}
		response = {}
		invoice = order.invoice_ids.filtered(lambda i: i.state=='draft') 
		session = self.env['pos.session'].browse(pos_order['pos_session_id'])
		config = session.config_id
		code = '01' if invoice.partner_id.is_company else '03'
		type_doc = self.env['einvoice.catalog.01'].search([('code','=',code)],limit=1) 
		# FIXME Siempre será una factura??
		invoice.write({'it_type_document':type_doc and type_doc.id or False})
		series = False 
		exchange_aux = 0.0 # tipo de cambio
		if code=='01' and config.invoice_series_id:
			series = config.invoice_series_id
		elif code=='03' and config.boleta_series_id:
			series = config.boleta_series_id
		if series:
			invoice.write({'serie_id':series.id})
			invoice.onchange_serie_id()
			if invoice.reference:
				invoice.with_context(prevent_send_einvoice=True).action_invoice_open()
				# pago con nota de crédito:
				#refund_ids=filter(lambda l: l[2]['inv_refund_applied_id'],pos_order['statement_ids'])
				statement_vals =  map(lambda l: l[2],pos_order['statement_ids'])
				# sólo positivos 
				#print('statement_vals',statement_vals)
				statement_vals = [stm for stm in statement_vals if stm['amount_currency']>0.0]
				#print('statement_vals',statement_vals)
				#refund_ids = filter(lambda l: ['inv_refund_applied_id'],statement_vals)
				refund_ids = map(lambda l: l['inv_refund_applied_id'],statement_vals)
				refund_ids = [i_id for i_id in refund_ids if i_id]
				if any(refund_ids):
					refund_inv=self.env['account.invoice'].browse(refund_ids).exists()
					for ref_inv in refund_inv.filtered('account_ids'):
						# FIXME Siempre será el primer item de los docs relacionados??
						# Esta mrd no es lo más óptimo pero debería funcionar xdxd
						aux = ref_inv.account_ids[0].comprobante
						ref_inv.account_ids[0].comprobante = invoice.number
						ref_inv.genera_asiento_nota_credito()
						ref_inv.account_ids[0].comprobante = aux
						if invoice.has_outstanding:
							json_data = json.loads(invoice.outstanding_credits_debits_widget)
							content = json_data.get('content',False)
							if content: 
								# FIXME Ver que pasa cuando son más de 2 items 
								invoice.refresh()
								invoice.assign_outstanding_credit(content[0]['id'])
				#Register payments
				try:
					pen = self.env['res.currency'].search_read([('name','=','PEN')],['id'],limit=1)[0]['id']
				except IndexError:
					pen = self.env.user.company_id.currency_id.id
				# dict medios de pago:
				means_dict = {
					'debit_card':'005',
					'credit_card':'006',
					'deposit':'001',
					'cheque':'007',
				}
				MeansPay = self.env['einvoice.means.payment']
				Payment  = self.env['account.payment']
				Journal  = self.env['account.journal']
				for st in statement_vals:
					if st.get('inv_refund_applied_id',False): continue
					jr = Journal.browse(st['journal_id'])
					payment_methods = jr.inbound_payment_method_ids
					pm = payment_methods and payment_methods[0].id or 1
					
					cred_info = st.get('credit_card_info')
					inv_refund_applied_id = st.get('inv_refund_applied_id')
					comprobante = st.get('pos_voucher_ref',st.get('pos_deposit_number',st.get('pos_cheque_number',False)))
					pay_in_usd = bool(st.get('payed_usd'))
					exchange_type = st['exchange_type'] if pay_in_usd else 1.0
					exchange_aux = max(exchange_type,exchange_aux)

					vals = {
						'journal_id':jr.id,
						#'amount':st['amount'],
						'payment_type':'inbound',
						'currency_id': jr.currency_id and jr.currency_id.id or pen,
						'date':fields.Date.context_today(self),
						'invoice_ids':[(6,0,[invoice.id])],
						'communication':invoice.number,
						'payment_method_id':pm,
						'partner_type':'customer',
						'it_type_document': type_doc and type_doc.id or False,
						'partner_id': pos_order['partner_id'],
						'amount':st['amount_currency'], # NOTE mandar siempre el amount curr
						'nro_caja': comprobante,
						'nro_comprobante': invoice.number,
						'check_currency_rate':pay_in_usd,
						'change_type':exchange_type,
						# POS fields:
						'pos_inv_refund_applied_id': int(inv_refund_applied_id) if inv_refund_applied_id else False,
						'pos_card_number': st.get('card_number',False),
						'pos_credit_card_info': int(cred_info) if cred_info else False,
						'pos_voucher_ref': st.get('voucher_ref',False),
						'pos_exchange_type': st.get('exchange_type',False),
						'pos_payed_usd': bool(st.get('payed_usd')),
						'pos_deposit_number': st.get('deposit_number',False),
						'pos_finacial_entity': st.get('finacial_entity',False),
						'pos_cheque_number': st.get('cheque_number',False),
						'pos_is_deferred': bool(st.get('is_deferred')),
						'pos_cheque_date_deferred': st.get('cheque_date_deferred',False),
					}
					pay = Payment.create(vals)
					method = jr.pos_pay_method
					if method and method in means_dict.keys():
						means_pay = MeansPay.search([('code','=',means_dict[method])],limit=1)
						pay.means_payment_id = means_pay and means_pay.id or False
					pay.post()
				ebill_res = invoice.make_einvoice() # la factura no necesariamente falló pero el documento no puede procesarse en NB
				if 'error' in ebill_res:
					response.update({
					'title': u'Error en Validación de factura electrónica',
					'status':'warning',})
					#return response

		# data para el ticket:
		#now = fields.Datetime.context_timestamp(self,datetime.now())
		now = datetime.now()
		type_sale = 'C. PAGO: %s // %s'%(order.payment_term_id.name or '',('V. DIRECTA' if order.is_direct_sale else ''))
		lines = order.order_line
		if 'title' not in response:
			response['title'] = u'Factura %s creada y validada.'%invoice.number
		if 'status' not in response:
			response['status'] = 'success'
		response.update({
			'invoice_id':invoice.id,
			'move_id':invoice.move_id.id,
			'order_data':{
				'date_order':str(now)[:19],
				'type_sale':type_sale,
				'ov_name':'%s - %s'%(pos_order['name'],order.name or ''),
				'partner':order.partner_id.name or '',
				'invoice':invoice.number or '',
				'partner_document':order.partner_id.nro_documento or '',
				'partner_street':order.partner_id.street or '',
				'partner_phone':order.partner_id.phone or '',
				'partner_mobile':order.partner_id.mobile or '',
				'amount_paid':pos_order['amount_paid'],
				'amount_untaxed':order.amount_untaxed,
				'amount_tax':pos_order['amount_tax'],
				'amount_return':pos_order['amount_return'],
				'amount_total':pos_order['amount_total'],
				'nro_items':len(lines.mapped('product_id')),
				'tc':exchange_aux,# le pongo el real o lo ocultamos
				'cashbox_name': config.name or '',
				'order_name':pos_order['name'],
				'hash_ebill':ebill_res.get('hash_ebill',''),
				'url_pdf':ebill_res.get('url_pdf',''),
				'cadena_qr':ebill_res.get('cadena_qr',''),
				'url_pdf2':ebill_res.get('url_pdf2',''),
				'item_lines':[
							{'quantity':l.product_uom_qty,
							'price_unit':l.price_unit,
							'discount':l.discount,
							'subtotal':l.price_subtotal,
							'product':l.product_id.name,} 
							for l in lines],
				}
			})
		return response


