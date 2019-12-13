# -*- coding: utf-8 -*-

from odoo import fields, models,api, _
from odoo.exceptions import UserError
from datetime import datetime

class StockMove(models.Model):
	_inherit='stock.move'

	retazo_origen = fields.Char('Retazo Origen', compute="getretazo_product_id")
	glass_order_line_ids = fields.Many2many('glass.order.line','glass_order_line_stock_move_rel','stock_move_id','glass_order_line_id',string='Glass Order Lines',copy=False)
	show_break_button   = fields.Boolean('Mostrar', compute='_get_show_break_button')
	show_detail_button  = fields.Boolean('Mostrar', compute='_get_show_detail_button')
	show_deliver_button = fields.Boolean('Mostrar', compute='_get_show_deliver_button')
	scrap_record_id = fields.Many2one('glass.scrap.record','move_id')
	# Visualizar los botones en funcion a si es un albaran de entrada o de salida:
	@api.depends('picking_id')
	def _get_show_break_button(self):
		for rec in self:
			rec.show_break_button = bool(rec.picking_id.apt_in)

	@api.depends('glass_order_line_ids','picking_id')
	def _get_show_detail_button(self):
		for rec in self:
			rec.show_detail_button = bool(len(rec.glass_order_line_ids) > 0 and rec.picking_id.state == 'done')

	@api.depends('procurement_id')
	def _get_show_deliver_button(self):
		for rec in self:
			rec.show_deliver_button = bool(rec.procurement_id.sale_line_id and rec.picking_id.state != 'done')

	@api.one
	@api.depends('product_id')
	def getretazo_product_id(self):
		cad=""
		if self.product_id:
			if self.product_id.uom_id.is_retazo:
				cad=str(self.product_id.uom_id.ancho)+"x"+ str(self.product_id.uom_id.alto)
				self.retazo_origen = cad

	# Obtiene los del detalle de los cristales que conforman 
	# el stock_move de salida (para entrega a clientes)
	def get_results(self):
		self.ensure_one()
		#calc_line_ids = self.procurement_id.sale_line_id.id_type.id_line.ids
		#lines = self.env['glass.order.line'].search([('calc_line_id','in',calc_line_ids)])
		#lines = lines.filtered(lambda x: not x.state == 'cancelled')
		wizard = self.env['glass.lines.for.move.wizard'].create({
			'move_glass_wizard_line_ids':[(0,0,{
				'move_id':self.id,
				'glass_line_id':l.id,
				'lot_line_id':l.lot_line_id.id,
				}) for l in self._get_calc_crystals_results()]
			})
		module = __name__.split('addons.')[1].split('.')[0]
		return {
			'name': 'Seleccionar Cristales',
			'res_id': wizard.id,
			'type': 'ir.actions.act_window',
			'res_model': wizard._name,
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': self.env.ref('%s.glass_lines_for_move_wizard_form_view' % module,False).id,
			'target': 'new',
		}

	def _get_calc_crystals_results(self):
		lines = self.procurement_id.sale_line_id.get_glass_order_lines()
		return lines.filtered(lambda x: not x.state == 'cancelled')

	# ver cristales para devolverse a produccion por rotura
	@api.multi
	def get_crystals_list_for_return(self):
		wizard = self.env['detail.crystals.entered.wizard'].create({})
		for line in self.glass_order_line_ids:
			wizard_line = self.env['detail.crystals.entered.wizard.line'].create({
				'wizard_id':wizard.id,
				'move_id':self.id,
				'glass_line_id':line.id,
				'lot_line_id':line.lot_line_id.id if line.lot_line_id else line.last_lot_line.id,
			})
		
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.show_detail_return_lines_wizard_form' % module)
		return {
			'name': 'Escoger Cristales a Romper o Devolver',
			'res_id': wizard.id,
			'type': 'ir.actions.act_window',
			'res_model': 'detail.crystals.entered.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'views': [(view.id, 'form')],
			'target': 'new',
		}
		
	# Detalle de los cristales que conforman el stock_move,
	@api.multi
	def get_detail_lines_entered_to_stock(self):
		wizard = self.env['detail.crystals.entered.wizard'].create({})
		for line in self.glass_order_line_ids:
			wizard_line = self.env['detail.crystals.entered.wizard.line'].create({
				'wizard_id':wizard.id,
				'move_id':self.id,
				'glass_line_id':line.id,
				'lot_line_id':line.lot_line_id.id if line.lot_line_id else line.last_lot_line.id,
			})
		
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.show_detail_lines_entered_stock_wizard' % module)
		return {
			'name': 'Detalle de Cristales',
			'res_id': wizard.id,
			'type': 'ir.actions.act_window',
			'res_model': 'detail.crystals.entered.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'views': [(view.id, 'form')],
			'target': 'new',
		}
