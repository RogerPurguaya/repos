# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	@api.constrains('before_invoice')
	def _verify_templates_in_calc_lines(self):
		for order in self.filtered('before_invoice'):
			bad_lines = order.order_line.mapped('calculator_id').filtered('template_id')
			if bad_lines:
				raise ValidationError(u'Las siguientes líneas de pedido tienen calculadoras asociadas a fichas maestras:\n%s\nSi desea hacer un pedido con factura adelantada debe remover dichas líneas'%'\n- '.join(bad_lines.mapped('product_id.name')))

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'
	
	def _prepare_calculator_vals(self):
		self.ensure_one()
		res = super(SaleOrderLine,self)._prepare_calculator_vals()
		product = self._context.get('defined_product',self.product_id)
		try:
			conf = self.env['mtf.parameter.config'].search([],limit=1)[0]
		except IndexError:
			raise UserError(u'No se han encontrado los parámetros de configuración para producción de cristales!')
		
		template = self.env['mtf.template'].search([('product_id','=',product.id)],limit=1)
		before_invoice = self.order_id.before_invoice
		if product.categ_id==conf.category_insulados_id:
			if not template: # si es insulado debe tener ficha
				raise UserError(u'No se ha encontrado una ficha maestra para el producto %s.\nPor favor solicite a su administrador crear una para dicho producto y así poder calcular el precio de su pedido.'%product.name)
			if before_invoice:
				raise UserError(u'No es posible generar un pedido con factura adelantada para un Cristal Insulado.')
			module = __name__.split('addons.')[1].split('.')[0]
			module = self._context.get('module_name',module)
			return {
				'vals': {
					'order_line_id':self.id,
					'type_calculator':'insulado_calculator',
					'template_id':template.id
					},
				'view': '%s.glass_calculator_insulados_form_view'%module,
				'act_name':'Calculadora de Insulados',
			}
		if template and not self.calculator_id: #si hay template y la calculadora recién será creada
			if before_invoice:
				raise UserError(u'El producto %s tiene asociada una Ficha Maestra.\nNo es posible generar calculadora si el pedido de venta es de factura adelantada y si dicho producto tiene asociada una Ficha Maestra'%product.name)
			else:
				res['vals']['template_id'] = template.id
		return res
		
		# if product.categ_id==conf.category_insulados_id:
		# 	template = self.env['mtf.template'].search([('product_id','=',product.id)],limit=1)
		# 	if not template:
		# 		raise UserError(u'No se ha encontrado una ficha maestra para el producto %s.\nPor favor solicite a su administrador crear una para dicho producto y así poder calcular el precio de su pedido.'%product.name)
		# 	module = __name__.split('addons.')[1].split('.')[0]
		# 	module = self._context.get('module_name',module)
		# 	res = {
		# 		'vals': {
		# 			'order_line_id':self.id,
		# 			'type_calculator':'insulado_calculator',
		# 			'template_id':template.id
		# 			},
		# 		'view': '%s.glass_calculator_insulados_form_view'%module,
		# 		'act_name':'Calculadora de Insulados',
		# 	}

		#	calculate = self.env['mtf.sale.calculate']
		# 	if self.mtf_calcutale_id:
		# 		calculate = self.mtf_calcutale_id
		# 	else:
		# 		calculate = calculate.create({'order_line_id':self.id,'template_id':template.id})
		# 		self.mtf_calcutale_id = calculate.id
		# 	module = __name__.split('addons.')[1].split('.')[0]
		# 	view = self.env.ref('%s.mtf_sale_calculate_view_form'%module)
		# 	return {
		# 		'name':'Calculadora de Insulados',
		# 		'res_id': calculate.id,
		# 		'type': 'ir.actions.act_window',
		# 		'res_model': calculate._name,
		# 		'view_id': view.id,
		# 		'view_mode': 'form',
		# 		'view_type': 'form',
		# 		'target': 'new',
		# 		}
		# return super(SaleOrderLine,self).show_calculator()

		