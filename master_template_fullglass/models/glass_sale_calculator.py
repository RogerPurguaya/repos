# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import re

class GlassSaleCalculator(models.Model):
	_inherit = 'glass.sale.calculator'

	type_calculator = fields.Selection(selection_add=[('insulado_calculator','Calculadora de Insulados')])
	template_id = fields.Many2one('mtf.template',string='Plantilla Maestra',readonly=True)
	
	def save_calculator(self):
		# update quantity and unit price
		res = super(GlassSaleCalculator,self).save_calculator()
		if self.template_id and not self.order_id.before_invoice:
			self.line_ids.compute_saleprice_from_template() # compute  from template
			total = sum(self.line_ids.mapped('mtf_sale_price'))
			if self.type_calculator=='insulado_calculator':
				self.order_line_id.write({
					'product_uom_qty':self.total_sold_area,
					'price_unit': total/self.total_sold_area
				})
			elif self.type_calculator=='common_product':
				self.order_line_id.write({
					'product_uom_qty':self.total_sold_area,
					'price_unit': total/self.total_sold_area
				})
			elif self.type_calculator=='service': # esta mrd cómo va a funcionar?
				self.order_line_id.write({
					'product_uom_qty':self.total_sold_area,
					'price_unit': total/self.total_sold_area
				})
		return res 
	
	def _get_glass_order_ids(self):
		ops = super(GlassSaleCalculator,self)._get_glass_order_ids()
		#add op's for child_ids
		return ops | self.line_ids.mapped('child_ids.glass_order_id')

	def _get_lines_to_produce(self):
		self.ensure_one()
		if self.type_calculator=='insulado_calculator':
			return self.line_ids.mapped('child_ids').filtered(lambda l: not l.glass_order_id)
		return super(GlassSaleCalculator,self)._get_lines_to_produce()

	# @api.constrains('line_ids')
	# def _verify_line_ids(self):
	# 	for rec in self.filtered(lambda x: x.type_calculator=='insulado_calculator'):
	# 		key_func = lambda x: x.child_ids.glass_order_id
	# 		grouped = x.child_ids.mapped('glass_order_id')
	# 		for group in grouped:
	# 			filt = rec.child_ids.filtered(lambda x: x.glass_order_id==group)
	# 			crystal_nums=list(chain(*[x.get_crystal_numbers() for x in filt]))
	# 			if crystal_nums != list(set(crystal_nums)):
	# 				raise UserError(u'Existen cristales con números duplicados en su calculadora de cristales insulados.')
	# 	return super(GlassSaleCalculator,self)._verify_line_ids()

	# En un principio la ficha maestra sólo era para insulados 
	#
	# @api.multi
	# def write(self, values):
	# 	if 'type_calculator' in values and values['type_calculator']!='insulado_calculator':
	# 		values['template_id'] = False
	# 	return super(GlassSaleCalculator,self).write(values)
	
class GlassSaleCalculatorLine(models.Model):
	_inherit = 'glass.sale.calculator.line'

	parent_id = fields.Many2one('glass.sale.calculator.line',string='Parent id',ondelete='cascade',help=u'Cristal Insulado Padre')
	template_id = fields.Many2one(related='calculator_id.template_id')
	child_ids = fields.One2many('glass.sale.calculator.line','parent_id',string='Childs',help=u'Cristales que conforman un Cristal Insulado')
	insulado = fields.Boolean('Insulado',help=u'Define si es un cristal insulado')
	from_insulado = fields.Boolean('Insulado',help=u'Define si forma parte de un cristal insulado')
	material_line_ids = fields.One2many('mtf.requisition.material.line','calculator_line_id')
	
	"""Importante: Este campo representa al cristal-producto (ejm Templado incoloro 8mm) 
	base para fabricar un insulado, no representa al producto Insulado en si, 
	solo debe ser seteado en registros de tipo child_ids."""
	product_ins_id = fields.Many2one('product.product',string=u'Cristal base de Insulado')
	default_code_ins = fields.Char(related='product_ins_id.default_code',string=u"Código")

	mtf_sale_price = fields.Float('Precio Total')

	_sql_constraints = [('check_insulado_is_not_child','CHECK ((insulado AND from_insulado)=false)',u'Un cristal no puede ser un insulado y proceder de un insulado a la vez!')]

	def validate_crystal_number(self,string,qty):
		# si es insulado se hace una verificación simple, ya que no es ingresada manualmente
		if self.from_insulado:
			numbers = []
			if re.match(r'\b[0-9]{1,}.[0-9]{1,}-[0-9]{1,}.[0-9]{1,}\b',string,re.I):
				nums = string.split('-')
				start,end = float(nums[0]),float(nums[1])
				if start>=end:
					return u'Formato de número de cristal insulado incorrecto: '+string
				while start<=end:
					numbers.append(start)
					start+=1
			elif re.match(r'(?<=^|)\d+\.\d+(?=$|)',string,re.I):
				numbers = [float(string)]
			else:
				return u'Formato de número de cristal insulado incorrecto: '+string
			if len(numbers)!=qty:
				return u"El número de cristales debe corresponder a la cantidad indicada (%d):\nValor ingresado: %s"%(qty,string)
			return numbers
		else:
			return super(GlassSaleCalculatorLine,self).validate_crystal_number(string,qty)
			

	
	def show_template_details(self):
		self.ensure_one()
		#if self.calculator_id.type_calculator!='insulado_calculator' or not self.calculator_id.template_id:
		if not self.template_id:
			raise UserError(u'Ésta calculadora no tiene una ficha maestra para el producto procesado.')
		module = __name__.split('addons.')[1].split('.')[0]
		return {
			'name':'Detalles de Ficha Maestra',
			'res_id':self.id,
			'type': 'ir.actions.act_window',
			'res_model': self._name,
			'view_id': self.env.ref('%s.calculator_line_template_details_form'%module).id,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
			}

	def _get_not_costed_lines(self):
		return self.material_line_ids.filtered('not_cost') 
	
	def compute_saleprice_from_template(self):
		"""Tengo en cuenta que los cristales insulados no tienen descuadre y son regulares
		PD: si ya existe un cristal con el mismo nro no es necesario crearlo de nuevo
		PD: si ya existe una línea de material con el mismo template_id no es necesario crearlo de nuevo
		PD: Si hay menos nuevos records que los existentes, eliminarlos"""
		for rec in self:
			if rec.calculator_id.is_locked:
				raise UserError(u'No es posible grabar una calculadora en estado bloqueado.')
			ctx = self._context.copy()
			ctx.update({
				'base':rec.base1,
				'height':rec.height1,
				'all_line_values':True,
				'not_costed_lines':rec.material_line_ids.filtered(lambda x: x.not_cost).ids
				})
			not_costed = rec._get_not_costed_lines()
			if not_costed:
				ctx['not_costed_lines'] = not_costed.mapped('template_line_id').ids
			sale_price,line_vals = rec.calculator_id.template_id.with_context(ctx).compute_template()
			to_production,materials,child_vals,material_vals = [],[],[],[]

			#to_production = sorted(to_production,key=lambda x: x[1]['pos_ins_crystal'])
			# for item in line_vals.items():
			# 	if item[1]['to_produce']:
			# 		to_production.append(item)
			# 	else:
			# 		materials.append(item)
			
			# Sólo los cristales insulados deberían tener child_ids
			for item in line_vals.items():
				if item[1]['pos_ins_crystal']:
					to_production.append(item)
				#else:
				materials.append(item)

			to_production = sorted(to_production,key=lambda x: x[1]['pos_ins_crystal'])

			nums = rec.get_crystal_numbers()
			mx = max(nums)
			mn = min(nums)
			for i,item in enumerate(to_production,1):
				key,value = item
				crystal_num = '%d.%d'%(mn,i) if mn==mx else '%d.%d-%d.%d'%(mn,i,mx,i)
				exist = rec.child_ids.filtered(lambda x: x.crystal_num==crystal_num)
				vals = {
					'product_ins_id':value['product_id'],
					'base1': value['base'],
					'base2': value['base'],
					'height1': value['height'],
					'height2': value['height'],
					'insulado':False,
					'from_insulado':True,
					'descuadre': rec.descuadre,
					'page_number':rec.page_number,
					'lavado':rec.lavado,
					'arenado':rec.arenado,
					'polished_id':rec.polished_id.id or False,
					'packed':rec.packed,
					'entalle':rec.entalle or False,
					'quantity':rec.quantity,
					'crystal_num':crystal_num,
					}
				if exist:
					child_vals.append((1,exist.id,vals))
				else:
					child_vals.append((0,0,vals))

			if rec.child_ids:
				map_nums = map(lambda x: x[2]['crystal_num'],child_vals)
				to_remove = rec.child_ids.filtered(lambda x: x.crystal_num not in map_nums)
				to_remove.unlink()
			
			for item in materials:
				key,value = item
				exist = rec.material_line_ids.filtered(lambda x: x.template_line_id.id==key)
				vals = {
					'template_line_id': key,
					'product_id': value['product_id'],
					'required_quantity': value['total_units'],
					}
				if exist:
					material_vals.append((1,exist.id,vals))
				else:
					material_vals.append((0,0,vals))

			if rec.material_line_ids:
				tmpl_line_ids = map(lambda x: x[2]['template_line_id'],material_vals)
				# remover los sobrantes, pero no los que se marcaron como no costeados
				to_remove = rec.material_line_ids.filtered(lambda x: x.template_line_id.id not in tmpl_line_ids and not x.not_cost)
				to_remove.unlink()

			rec.write({
				'child_ids':child_vals,
				'material_line_ids':material_vals,
				'mtf_sale_price':sale_price * rec.quantity,
			})
		return {"type": "ir.actions.do_nothing",} 

class MtfRequisitionMaterialLine(models.Model):
	_name = 'mtf.requisition.material.line'
	#_name = 'mtf.insulado.material.line'
	
	calculator_line_id = fields.Many2one('glass.sale.calculator.line',string=u'Línea de calculadora asociada',required=True,ondelete='cascade')
	#requisition_id = Many2one('mtf.requisition',string=u'Requisición')
	template_line_id = fields.Many2one('mtf.template.line',help=u'Línea de ficha maestra asociada')
	product_id = fields.Many2one(related='template_line_id.product_id')
	default_code = fields.Char(related='template_line_id.default_code')
	model  = fields.Char(related='template_line_id.model')
	uom_id = fields.Many2one(related='template_line_id.uom_id',string='Unidad')
	to_produce = fields.Boolean(related='template_line_id.to_produce')
	required_quantity = fields.Float('Cantidad Requerida',digits=(12,4),help=u'Cantidad de material necesario para fabricar la cantidad de cristal Insulado requerida')
	not_cost = fields.Boolean('No Costear',help=u'Marque ésta opción si no desea omitir esta línea, suele darse cuando el cliente trae materiales propios.')

	@api.multi
	def write(self,values):
		for rec in self:
			if rec.calculator_line_id.calculator_id.is_locked:
				raise UserError(u'No es posible editar la línea de requerimiento si la calculadora está bloqueada.')
			# send message:
			if values.get('not_cost',False):
				msg = u'Se estableció el producto de ficha maestra <a href=# data-oe-model=product.product data-oe-id=%d>%s</a> como no material propio y no costeado.'%(rec.product_id.id,rec.product_id.name)
				rec.calculator_line_id.calculator_id.order_id.message_post(body=msg)
		return super(MtfRequisitionMaterialLine,self).write(values)