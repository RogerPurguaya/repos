# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from itertools import groupby,chain

class GlassSaleCalculator(models.Model):
	_inherit = 'glass.sale.calculator'

	is_locked = fields.Boolean('Bloqueado',compute='_compute_locked')

	@api.multi
	def write(self,values):
		if self.is_locked and self._context.get('force_write') is None:
			raise UserError(u'No es posible editar una calculadora en estado bloqueado.')
		return super(GlassSaleCalculator,self).write(values)

	def save_calculator(self):
		if self.is_locked:
			raise UserError(u'No es posible grabar una calculadora en estado bloqueado.')
		return super(GlassSaleCalculator,self).save_calculator()

	@api.constrains('line_ids')
	def _verify_line_ids(self):
		"""Verificar si hay cristales con números duplicados en la calculadora.
		   Se agrupa por orden de producción ya que si es factura adelantada un cristal
		   puede repetir el número, siempre que esté en otra orden de producción.
		   Comment by Leo de Oz
		"""
		key_func = lambda x: x.glass_order_id
		for rec in self:
			data = rec.line_ids.sorted(key=key_func)
			for key,group in groupby(data,key_func):
				crystal_nums=list(chain(*[x.get_crystal_numbers() for x in list(group)]))
				if crystal_nums != list(set(crystal_nums)):
					raise UserError(u'Existen cristales con números duplicados en su calculadora de cristales.')

	@api.depends('order_id.state','line_ids')
	def _compute_locked(self):
		for rec in self:
			op_ids = rec._get_glass_order_ids()
			if rec.order_id.state=='draft' and not op_ids:
				rec.is_locked = False
			else:
				if rec.order_id.before_invoice:
					if not rec._get_lines_to_produce() and rec.qty_invoiced_rest <= 0:
						rec.is_locked = True
					else:
						rec.is_locked = False
				else:
					rec.is_locked = True

	def _get_glass_order_ids(self):
		"""Método para redefinir en la calculadora de insulados"""
		self.ensure_one()
		return self.line_ids.mapped('glass_order_id')

	def _get_lines_to_produce(self):
		"""Obtener las líneas de calculadora para generar O.P.
		método heredable para agregar lógica adicional, por defecto retornamos las líneas de calculadora
		que no tienen 'glass_order_id'"""
		self.ensure_one()
		return self.line_ids.filtered(lambda l: not l.glass_order_id)


class GlassSaleCalculatorLine(models.Model):
	_inherit = 'glass.sale.calculator.line'

	glass_order_id = fields.Many2one('glass.order',string=u'Órden de producción')
	# crystal stages
	entalle = fields.Integer('Entalle')
	lavado = fields.Boolean('Lavado')
	arenado = fields.Boolean('Arenado')
	polished_id = fields.Many2one('sale.pulido.proforma',u'Pulido')

	@api.model
	def default_get(self,default_fields):
		res = super(GlassSaleCalculatorLine,self).default_get(default_fields)
		try:
			conf = self.env['glass.order.config'].search([])[0]
		except IndexError:
			raise UserError(u'No se encontraron los valores de configuración de producción')
		if conf.default_pulido:
			res.update({'polished_id': conf.default_pulido.id})
		return res

	@api.multi
	def unlink(self):
		if self.filtered('glass_order_id'):
			raise UserError(u'No es posible eliminar una línea de calculadora cuando tiene un OP asociada')
		return super(GlassSaleCalculatorLine,self).unlink()
	