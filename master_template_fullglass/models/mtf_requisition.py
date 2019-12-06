# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class MtfRequisition(models.Model):
	_name = 'mtf.requisition'

	_description = u'Requisición de materiales para productos con ficha maestra.'

	name = fields.Char('Nombre')
	user_id = fields.Many2one('res.users',string='Responsable')
	line_ids = fields.One2many('mtf.requisition.line','requisition_id')
	state = fields.Selection([('draft','Borrador'),('confirmed','Confirmada'),('ended','Finalizada')],default='draft',string='Estado')

	
	#picking_ids = fields.Many2many('stock.picking',string='Pickings',compute='_get_picking_ids',copy=False)
	#picking_count = fields.Integer(u'Nro pickings',compute="_get_picking_ids",copy=False)
	# @api.one
	# def _get_picking_ids(self):
	# 	ops = self.env['glass.order'].search([('sale_order_id','=',self.id),('state','=','returned')])
	# 	self.op_returned_count=len(ops)
	# 	self.op_returned_ids=ops.ids

class MtfRequisition(models.Model):
	_name = 'mtf.requisition.line'

	_description = u'Requisición de materiales de Op.'

	requisition_id = fields.Many2one('mtf.requisition',string=u'Requisición',ondelete='cascade',required=True)
	product_id = fields.Many2one('product.product',string='Producto')
	default_code = fields.Char(related='product_id.default_code')
	uom_id = fields.Many2one(related='product_id.uom_id',string='Unidad')
	quantity = fields.Float('Cantidad',digits=(12,4),help=u'Cantidad a requerir')
	qty_done = fields.Float('Cantidad realizada',digits=(12,4))

