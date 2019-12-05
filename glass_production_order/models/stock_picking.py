# -*- coding: utf-8 -*-
from odoo import fields, models,api
from odoo.exceptions import UserError
from datetime import datetime

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	sale_picking = fields.Boolean() # # para checar que la etrega es por cristales
	driver_delivery=fields.Char('Conductor')
	apt_in = fields.Boolean() # si es albaran de ingreso a apt

	@api.multi
	def action_revert_done(self):
		reqs = self.env['glass.requisition'].search([('state','in',('process','confirm'))])
		if self.id in reqs.mapped('picking_ids').ids:
			raise UserError(u'No es posible hacer Re-open de un Albarán de requisición!, debe cancelar la requisición!')
		t = super(StockPicking,self).action_revert_done()
		if any(self.move_lines.mapped('scrap_record_id')):
			for item in self.move_lines.mapped('scrap_record_id'):
				if item.type_move == 'in':
					qty = item.scrap_move_id.quantity # nro retazos
					item.scrap_move_id.write({'quantity':qty-item.pieces})
				elif item.type_move == 'out':
					qty = item.scrap_move_id.quantity # nro retazos
					item.scrap_move_id.write({'quantity':qty+item.pieces})
		return t
	
	@api.multi
	def do_new_transfer(self):
		t = super(StockPicking,self).do_new_transfer()
		pk = self._context.get('packing_list_transfer',False) # tranf. de packing list
		delivery = self._context.get('delivery_transfer',False) # transf por entrega
		# verifica que la entrega es por cristales y op:
		if self.sale_picking and not pk and not delivery:
			for move in self.move_lines:
				res = move.get_results()
				wizard = self.env['glass.lines.for.move.wizard'].browse(res['res_id'])		
				if len(wizard.move_glass_wizard_line_ids.mapped('glass_line_id').filtered(lambda x: x.state != 'send2partner')) > 0:
					raise UserError(u'No se han entregado todos los cristales del pedido de venta de este albarán!')
		
		# gestion de retazos cuando tranfieran el picking manualmente
		ctx = self._context.get('first_transaction',False) # cuando es prim trans no ejecuta
		if not ctx and any(self.move_lines.mapped('scrap_record_id')) and type(t) != dict:
			for item in self.move_lines.mapped('scrap_record_id'):
				if item.type_move == 'in':
					qty = item.scrap_move_id.quantity # nro retazos
					item.scrap_move_id.write({'quantity':qty+item.pieces})
				elif item.type_move == 'out':
					qty = item.scrap_move_id.quantity # nro retazos
					item.scrap_move_id.write({'quantity':qty-item.pieces})
		return t

class StockImmediateTransfer(models.TransientModel):
	_inherit = 'stock.immediate.transfer'
	
	@api.multi
	def process(self):
		self.ensure_one()
		t = super(StockImmediateTransfer,self).process()
		first = self._context.get('first_transaction',False) # primera transac
		if not first and any(self.pick_id.move_lines.mapped('scrap_record_id')):
			for item in self.pick_id.move_lines.mapped('scrap_record_id'):
				if item.type_move == 'in':
					qty = item.scrap_move_id.quantity # nro retazos
					item.scrap_move_id.write({'quantity':qty+item.pieces})
				elif item.type_move == 'out':
					qty = item.scrap_move_id.quantity # nro retazos
					item.scrap_move_id.write({'quantity':qty-item.pieces})
		return t
