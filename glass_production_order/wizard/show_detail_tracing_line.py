# -*- coding: utf-8 -*-
from odoo import fields,models,api,exceptions, _
from odoo.exceptions import UserError
from datetime import datetime
from functools import reduce

# Wizard contenedor para ver detalle sde una linea de seguimiento de producccion:
class Show_Detail_Tracing_Line_Wizard(models.TransientModel):
	_name = 'show.detail.tracing.line.wizard'
	
	lot_line_id = fields.Many2one('glass.lot.line','Lote')
	display_name_product = fields.Char(related='lot_line_id.product_id.name',string='Producto')
	lot_name = fields.Char(related='lot_line_id.lot_id.name',string='Lote')
	order_id = fields.Many2one(related='lot_line_id.order_prod_id')
	op_name = fields.Char(related='order_id.name')
	op_date_production = fields.Date(related='order_id.date_production')
	op_date_generate = fields.Datetime(related='order_id.date_order')
	op_date_send = fields.Date(related='order_id.date_send')
	op_date_delivery = fields.Date(related='order_id.date_delivery')
	invoice = fields.Many2one('account.invoice',string='Factura',compute='_get_invoice')
	invoice_number = fields.Char(string='Numero Factura',compute='_get_invoice')
	stages_lines_ids = fields.One2many(related='lot_line_id.stage_ids',string='Etapas de lote')
	# totales sacados de la op:
	count_required = fields.Integer('Nro Solicitados',compute='_get_required')
	area_required = fields.Float('Solicitados M2',compute='_get_required')
	count_produced = fields.Integer('Nro Producidos',compute='_get_produced')
	area_produced = fields.Float('Producidos M2',compute='_get_produced')
	search_code = fields.Char(related='lot_line_id.search_code')

	@api.depends('lot_line_id')
	def _get_invoice(self):
		for rec in self:
			invoice = rec.lot_line_id.order_prod_id.invoice_ids
			rec.invoice = invoice[0].id if invoice else False
			rec.invoice_number = invoice.number or u'Factura pendiente de validación'
	
	@api.depends('lot_line_id')
	def _get_required(self):
		for rec in self:
			rec.count_required = rec.lot_line_id.calc_line_id.calculator_id.total_pieces
			rec.area_required = rec.lot_line_id.calc_line_id.calculator_id.total_area
			#sale_lines = rec.order_id.sale_lines.filtered(lambda x: x.product_id.id == rec.lot_line_id.product_id.id)
			# if len(sale_lines) > 0:
			# 	rec.area_required = reduce(lambda x,y: x+y,sale_lines.mapped('product_uom_qty'))
			# 	qtys = sale_lines.mapped('id_type_line').mapped('cantidad')
			# 	if len(qtys) > 0:
			# 		rec.count_required = reduce(lambda x,y: x+y,qtys)
			# 	else:
			# 		rec.count_required = 0
			# else:
			# 	rec.area_required = False
			# 	rec.count_required = False

	@api.depends('order_id')
	def _get_produced(self):
		for rec in self:
			lot_lines = rec.order_id.line_ids.mapped('lot_line_id').filtered(lambda x: x.product_id == rec.lot_line_id.product_id)
			produced = lot_lines.filtered(lambda x: x.templado)
			rec.area_produced = sum(produced.mapped('area'))
			rec.count_produced = len(produced)



		






