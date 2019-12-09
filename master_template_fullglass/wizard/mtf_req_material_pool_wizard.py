# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class MtfRequisitionPoolWizard(models.TransientModel):
	_name='mtf.requisition.pool.wizard'
	
	seq_id = fields.Many2one('ir.sequence')
	picking_type_id = fields.Many2one('stock.picking.type',u'Tipo de Operación')
	req_traslate_motive = fields.Many2one('einvoice.catalog.12',u'Motivo de traslado')
	
	next_req_number = fields.Char(u'Sig Número')
	order_id = fields.Many2one('glass.order',u'Orden de producción',domain=lambda self: self._context.get('available_ops',[]))

	line_ids = fields.One2many('mtf.requisition.pool.wizard.line','wizard_id')
	user_id = fields.Many2one('res.users','Responsable',default=lambda self: self.env.uid)

	def get_new_element(self):
		conf = self.env['mtf.parameter.config'].search([],limit=1)
		seq_id = conf.requisition_seq_id
		if not seq_id:
			raise UserError(u'No ha configurado una secuencia para generar Orden de Requisición de materiales')
		ids = []
		available_ops=self.env['glass.order'].search([('state','in',('process','confirmed'))])
		available_ops=available_ops.filtered(lambda x: x.mtf_req_line_ids)
		for op in available_ops:
			if op.mtf_requirement_ids.filtered(lambda x: x.state!='cancel'):
				continue
			ids.append(op.id)
		new = self.create({
			'seq_id':seq_id.id,
			'next_req_number':seq_id.number_next_actual,
			'picking_type_id':conf.req_default_pick_type_id.id,
			'req_traslate_motive':conf.req_default_traslate_motive_id.id,
		})
		module = __name__.split('addons.')[1].split('.')[0]
		ctx = self._context.copy()
		ctx.update({'available_ops':[('id','in',ids)]})
		return {
			'name':'Pool de Ficha maestra/Insulados',
			'res_id':new.id,
			'type': 'ir.actions.act_window',
			'res_model': self._name,
			'view_id': self.env.ref('%s.mtf_requisition_pool_wizard_view_form'%module).id,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
			'context':ctx
			}

	def get_order_requirements(self):
		self.ensure_one()
		if self.order_id.mtf_requirement_ids.filtered(lambda x: x.state!='cancel'):
			raise UserError('La Orden de prod. %s ya tiene asignada Una Orden de requisición de Ficha Maestra para sus materiales'%self.order_id.name)
		req_lines = self.order_id.mtf_req_line_ids 
		products = req_lines.mapped('product_id')
		# grouped lines by product
		values = []
		self.line_ids.unlink()
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
		self.get_order_requirements()
		req = self.env['mtf.requisition'].create(self._prepare_req_vals())
		
		picking_vals = self._prepare_picking_vals()
		move_vals = [(0,0,self._prepare_move_vals(l)) for l in req.line_ids]
		
		picking_vals.update({'origin':req.name,'move_lines':move_vals,})
		
		pick = self.env['stock.picking'].create(picking_vals)
		pick.action_confirm()
		pick.action_assign()

		module = __name__.split('addons.')[1].split('.')[0]
		#self.order_id.mtf_req_line_ids.with_context(force_write=True).write({'requirement':True})
		return {
			'name':req.name,
			'res_id':req.id,
			'type': 'ir.actions.act_window',
			'res_model': req._name,
			'view_id': self.env.ref('%s.mtf_requisition_view_form'%module).id,
			'view_mode': 'form',
			'view_type': 'form',
			}
		
	def _prepare_req_vals(self):
		name = '%s/%s'%(self.seq_id.next_by_id(),self.order_id.name)
		return {
			'name': name,
			'user_id':self.user_id.id,
			'order_id':self.order_id.id,
			'state':'confirmed',
			'line_ids': [(0,0,{
				'product_id':l.product_id.id,
				'quantity':l.quantity,}) for l in self.line_ids]
		}

	def _prepare_picking_vals(self):
		current_date = fields.Date.context_today(self)
		pick_type = self.picking_type_id
		return {
			# TODO que partner le ponemos??
			# al parecer siempres serán transf. internas, si son incoming, asignar un partner 
			'partner_id':False,
			'picking_type_id':pick_type.id,
			'date':current_date,
			'fecha_kardex':current_date,
			'location_dest_id':pick_type.default_location_dest_id.id,
			'location_id': pick_type.default_location_src_id.id,
			'company_id': self.env.user.company_id.id,
			'einvoice_12': self.req_traslate_motive.id,
		}

	def _prepare_move_vals(self,req_line):
		current_date = fields.Date.context_today(self)
		pick_type = self.picking_type_id
		return {
		'name': req_line.product_id.name,
		'product_id': req_line.product_id.id,
		'product_uom': req_line.product_id.uom_id.id,
		'date':current_date,
		'date_expected':current_date,
		'picking_type_id': pick_type.id,
		'location_id': pick_type.default_location_src_id.id,
		'location_dest_id': pick_type.default_location_dest_id.id,
		'partner_id': False,
		'move_dest_id': False,
		'state': 'draft',
		'company_id':self.env.user.company_id.id,
		'procurement_id': False,
		'route_ids':pick_type.warehouse_id and [(6,0,pick_type.warehouse_id.route_ids.ids)] or [],
		'warehouse_id': pick_type.warehouse_id and pick_type.warehouse_id.id or False,
		'product_uom_qty':req_line.quantity,
		'mtf_requeriment_line_id':req_line.id,
		}


class MtfRequisitionPoolWizardLine(models.TransientModel):
	_name='mtf.requisition.pool.wizard.line'

	wizard_id = fields.Many2one('mtf.requisition.pool.wizard')
	product_id = fields.Many2one('product.product',string=u'Producto')
	default_code = fields.Char(related='product_id.default_code',string=u'Código')
	uom_id = fields.Many2one(related='product_id.uom_id',string='Unidad de Medida')
	quantity = fields.Float('Cantidad')
