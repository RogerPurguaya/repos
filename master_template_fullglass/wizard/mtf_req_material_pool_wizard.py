# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class MtfRequisitionPoolWizard(models.TransientModel):
	_name='mtf.requisition.pool.wizard'
	
	seq_id = fields.Many2one('ir.sequence')
	picking_type_id = fields.Many2one('stock.picking.type',u'Tipo de Operación')
	req_traslate_motive = fields.Many2one('einvoice.catalog.12',u'Motivo de traslado')
	
	next_req_number = fields.Char(u'Sig Número')
	order_id = fields.Many2one('glass.order',u'Orden de producción',
							domain=[('state','in',('process','confirmed')),('mtf_have_reqs','=',True)])
	
	line_ids = fields.One2many('mtf.requisition.pool.wizard.line','wizard_id')
	user_id = fields.Many2one('res.users','Responsable',default=lambda self: self.env.uid)



	@api.model
	def default_get(self, default_fields):
		res = super(MtfRequisitionPoolWizard,self).default_get(default_fields)
		conf = self.env['mtf.parameter.config'].search([],limit=1)
		seq_id = conf.requisition_seq_id
		if not seq_id:
			raise UserError(u'No ha configurado una secuencia para generar Orden de Requisición de materiales')
		res.update({
			'seq_id':seq_id.id,
			'next_req_number':seq_id.number_next_actual,
			'picking_type_id':conf.req_default_pick_type_id.id,
			'req_traslate_motive':conf.req_default_traslate_motive_id.id,
		})
		return res


	def get_order_requirements(self):
		self.ensure_one()
		if self.order_id.mtf_requirement_ids.filtered(lambda x: x.state!='cancel'):
			raise UserError('La Orden de prod. %s ya tiene asignada Una Orden de requisición de Ficha Maestra para sus materiales'%self.order_id.name)
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
		return {"type": "ir.actions.do_nothing",} 

	def create_req_order(self):
		self.ensure_one()


	def _prepare_req_vals(self):
		vals = {
			'name':self.seq_id.next_by_id(),
			'user_id':self.user_id.id,
			'order_id':self.order_id.id,
			'picking_id':1,
		}

	def _prepare_picking_vals(self):
		current_date = fields.Date.context_today(self)
		pick_type = self.picking_type_id
		return {
			'picking_type_id': pick_type.id,
			'partner_id':self.env.user.company_id.partner_id.id, # que parner le ponemos??
			'date': current_date,
			'fecha_kardex': current_date,
			#'origin': order.name,
			'location_dest_id': pick_type.default_location_dest_id.id,
			'location_id': pick_type.default_location_src_id.id,
			'company_id': self.env.user.company_id.id,
			'einvoice_12': self.req_traslate_motive.id,
		}





class MtfRequisitionPoolWizardLine(models.TransientModel):
	_name='mtf.requisition.pool.wizard.line'

	wizard_id = fields.Many2one('mtf.requisition.pool.wizard')
	product_id = fields.Many2one('product.product',string=u'Producto')
	default_code = fields.Char(related='product_id.default_code',string=u'Código')
	uom_id = fields.Many2one(related='product_id.uom_id',string='Unidad de Medida')
	quantity = fields.Float('Cantidad')
