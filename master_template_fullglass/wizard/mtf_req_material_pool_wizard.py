# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class GlassPoolWizard(models.TransientModel):
	_name='mtf.requisition.pool.wizard'

	line_order_ids = fields.Many2many('glass.order.line','glass_lines_wizard_rel','wizard_id','line_order_id')
	line_ids = fields.One2many('glass.pool.wizard.line','wizard_id')
	#prod_detail_id = fields.One2many('glass.pool.wizard.line.detail','wizard_id')
	#prod_detail_id_m = fields.Many2many('glass.pool.wizard.line.detail','glass_wizard_rel','wizard_id','detail_id')
	product_id = fields.Many2one('product.product',string=u'Producto Seleccionado')
	nextlotnumber = fields.Char('Lote')
	qty_lines = fields.Integer('Cantidad',compute="getarealines")
	area_lines = fields.Float(u'Área M2',compute="getqtyarea",digits=(20,4))
	user_id=fields.Many2one('res.users','Responsable')
	show_button = fields.Boolean('Show button',default=True)
	state = fields.Selection([('draft','Borrador'),('confirm','Confirmado')],string='Estado',default='draft')
	
class GlassPoolWizardLine(models.TransientModel):
	_name='glass.pool.wizard.line'

	#order_line_id = fields.Many2one('glass.order.line')
	wizard_id = fields.Many2one('glass.pool.wizard')
	product_id = fields.Many2one('product.product',string=u'Producto')
	default_code = fields.Char(related='product_id.default_code',string=u'Código')
	uom_id = fields.Many2one(related='product_id.uom_id',string='Unidad de Medida')
	qty = fields.Float('Cantidad')
	area = fields.Float('M2',digits=(20,4))
	selected = fields.Boolean('Seleccionado')
	area_rest = fields.Float(u'Área Restante M2',digits=(20,4))
	cant_rest = fields.Integer(u'Cantidad restante')