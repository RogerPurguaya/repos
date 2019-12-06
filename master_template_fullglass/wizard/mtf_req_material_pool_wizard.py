# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class MtfRequisitionPoolWizard(models.TransientModel):
	_name='mtf.requisition.pool.wizard'
	
	def _get_nextnumber(self):
		seq = self.env['mtf.parameter.config'].search([],limit=1).requisition_seq_id
		if not seq:
			raise UserError(u'No ha configurado una secuencia para generar Orden de Requisición de materiales')
		return seq.number_next_actual

	next_req_number = fields.Char('Lote',default=_get_nextnumber)
	
	order_id = fields.Many2one('glass.order',u'Orden de producción')
	
	line_ids = fields.One2many('mtf.requisition.pool.wizard.line','wizard_id')
	user_id = fields.Many2one('res.users','Responsable',default=lambda self: self.env.uid)

	def get_order_requirements(self):
		self.ensure_one()
		req_lines = self.order_id.mtf_req_line_ids 
		products = req_lines.mapped('product_id')
		# grouped lines by product
		values = []
		for product in products:
			filt = req_lines.filtered(lambda l: l.product_id==product)
			values.append((0,0,{
				'product_id':product.id,
				'quantity':sum(filt.mapped('required_quantity'))
			}))
		self.write({'line_ids':values})

class MtfRequisitionPoolWizardLine(models.TransientModel):
	_name='mtf.requisition.pool.wizard.line'

	wizard_id = fields.Many2one('mtf.requisition.pool.wizard')
	product_id = fields.Many2one('product.product',string=u'Producto')
	default_code = fields.Char(related='product_id.default_code',string=u'Código')
	uom_id = fields.Many2one(related='product_id.uom_id',string='Unidad de Medida')
	quantity = fields.Float('Cantidad')
