# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MtfRequisition(models.Model):
	_name = 'mtf.requisition'

	_description = u'Requisición de materiales para productos con ficha maestra.'

	name = fields.Char('Nombre')
	user_id = fields.Many2one('res.users',string='Responsable')
	order_id = fields.Many2one('glass.order',string=u'Orden de Producción')
	partner_id = fields.Many2one(related='order_id.partner_id',string=u'Cliente')
	line_ids = fields.One2many('mtf.requisition.line','requisition_id')
	state = fields.Selection([('draft','Borrador'),('confirmed','Confirmada'),('ended','Finalizada'),('cancel','Cancelada')],readonly=True,string='Estado',default='draft')

	picking_ids = fields.Many2many('stock.picking',compute='_compute_picking_ids',string='Albaranes')
	picking_count = fields.Integer(string='Nro Pickings',compute='_compute_picking_ids')

	@api.depends('line_ids')
	def _compute_picking_ids(self):
		for order in self:
			moves=self.env['stock.move'].search([('mtf_requeriment_line_id','in',order.line_ids.ids)])
			order.picking_ids = moves.mapped('picking_id')
			order.picking_count = len(order.picking_ids)

	@api.multi
	def action_view_pickings(self):
		action = self.env.ref('stock.action_picking_tree_all').read()[0]
		pickings = self.mapped('picking_ids')
		if len(pickings) > 1:
			action['domain'] = [('id', 'in', pickings.ids)]
		elif pickings:
			action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
			action['res_id'] = pickings.id
		return action

	#@api.depends('picking_ids')
	# @api.multi
	# def _compute_state(self):
	# 	"""Computar en base al estado de los albaranes"""
	# 	print('la ptm ',self)
	# 	for order in self:
	# 		print('la ptm ',order.picking_ids)
	# 		if not order.picking_ids:
	# 			order.state = 'draft'
	# 			return
	# 		if all(p.state=='done' for p in order.picking_ids):
	# 			order.state = 'ended'
	# 		elif all(p.state=='cancel' for p in order.picking_ids):
	# 			order.state = 'cancel'
	# 		else:
	# 			order.state = 'confirmed'

	def process_requisition(self):
		## Solo check si todos los albaranes fueron realizados:
		self.ensure_one()
		if self.picking_ids.filtered(lambda p: p.state!='done'):
			raise UserError(u'No es posible procesar esta requisición debido a que tiene albaranes asociados sin validar')
		self.state = 'ended'

	def cancel_requisition(self):
		self.ensure_one()
		if self.picking_ids.filtered(lambda p: p.state=='done'):
			raise UserError(u'Esta órden tiene asociados albaranes en estado realizado, debe realizar un extorno de la mercaderia transferida para poder cancelar esta requisición')
		self.picking_ids.action_cancel()
		self.state = 'cancel'
		return True

class MtfRequisition(models.Model):
	_name = 'mtf.requisition.line'

	_description = u'Requisición de materiales de Op.'

	requisition_id = fields.Many2one('mtf.requisition',string=u'Requisición',ondelete='cascade',required=True)
	product_id = fields.Many2one('product.product',string='Producto')
	default_code = fields.Char(related='product_id.default_code')
	uom_id = fields.Many2one(related='product_id.uom_id',string='Unidad')
	quantity = fields.Float('Cantidad',digits=(12,4),help=u'Cantidad a requerir')
	qty_done = fields.Float('Cantidad realizada',digits=(12,4))

