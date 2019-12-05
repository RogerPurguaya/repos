# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
	_inherit='sale.order'

	before_invoice = fields.Boolean('Factura Adelantada',default=False)

	@api.one
	def unlink(self):
		if self.invoice_count>0:
			raise UserError(u"No se puede eliminar un pedido de venta si ya fue facturado")
		# for l in self.order_line:
		# 	if l.id_type:
		# 		raise UserError(u"No se puede eliminar un pedido de venta si tiene calculadora")
		return super(SaleOrder,self).unlink()

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	calculator_id = fields.Many2one('glass.sale.calculator',string='Calculadora')

	def show_calculator(self):
		self.ensure_one()
		calculator = self.env['glass.sale.calculator']
		values = self._prepare_calculator_vals() 
		if self.calculator_id:
			calculator = self.calculator_id
		else:
			calculator = calculator.create(values['vals'])
			self.calculator_id = calculator.id
		return {
			'name':values['act_name'],
			'res_id': calculator.id,
			'type': 'ir.actions.act_window',
			'res_model': calculator._name,
			'view_id': self.env.ref(values['view']).id,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
			}

	def _prepare_calculator_vals(self):
		self.ensure_one()
		product = self._context.get('defined_product',self.product_id)
		module_name = self._context.get('module_name',(__name__.split('addons.')[1].split('.')[0]))
		if product.type == 'service':
			return {
				'vals': {'order_line_id':self.id,'type_calculator':'service'},
				'view': '%s.glass_calculator_services_form'%module_name,
				'act_name':'Calculadora de Servicios',
			}
		else:
			return {
				'vals': {'order_line_id':self.id,'type_calculator':'common_product'},
				'view': '%s.glass_calculator_form_view'%module_name,
				'act_name':'Calculadora de cristales',
			}

	@api.multi
	def write(self,values):
		if 'product_id' in values and self.calculator_id:
			prod = self.env['product.product'].browse(values['product_id'])
			self.calculator_id.type_calculator = self.with_context(defined_product=prod)._prepare_calculator_vals()['vals']['type_calculator']
		return super(SaleOrderLine,self).write(values)


