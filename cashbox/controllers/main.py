# -*- coding: utf-8 -*-
import json
import logging
import werkzeug.utils

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CashboxController(http.Controller):
#class PosController(http.Controller):

	# @http.route('/pos/web', type='http', auth='user')
	# def pos_web(self, debug=False, **k):
	# 	# if user not logged in, log him in
	# 	pos_sessions = request.env['pos.session'].search([
	# 		('state', '=', 'opened'),
	# 		('user_id', '=', request.session.uid),
	# 		('name', 'not like', '(RESCUE FOR')])
	# 	if not pos_sessions:
	# 		return werkzeug.utils.redirect('/web#action=point_of_sale.action_client_pos_menu')
	# 	pos_sessions.login()
	# 	context = {
	# 		'session_info': json.dumps(request.env['ir.http'].session_info())
	# 	}
	# 	return request.render('point_of_sale.index', qcontext=context)

	@http.route('/cashbox/web', type='http', auth='user')
	def cashbox_web(self, debug=False, **k):
		# if user not logged in, log him in
		cashbox_sessions = request.env['cashbox.session'].search([
			('state', '=', 'opened'),
			('user_id', '=', request.session.uid),
			('name', 'not like', '(RESCUE FOR')])
		if not cashbox_sessions:
			return werkzeug.utils.redirect('/web#action=cashbox.action_client_cashbox_menu')
		cashbox_sessions.login()
		context = {
			'session_info': json.dumps(request.env['ir.http'].session_info())
		}
		return request.render('cashbox.index', qcontext=context)


	# report??
	# @http.route('/cashbox/sale_details_report', type='http', auth='user')
	# def print_sale_details(self, date_start=False, date_stop=False, **kw):
	# 	r = request.env['report.cashbox.report_saledetails']
	# 	pdf = request.env['report'].with_context(date_start=date_start, date_stop=date_stop).get_pdf(r, 'cashbox.report_saledetails')
	# 	pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
	# 	return request.make_response(pdf, headers=pdfhttpheaders)
