# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from decimal import Decimal
import re,os,base64
import PIL.ImageDraw as ImageDraw
import PIL.Image as Image
from PIL import ImageFont

class GlassSaleCalculator(models.Model):
	_name = 'glass.sale.calculator'

	order_line_id = fields.Many2one('sale.order.line',ondelete='cascade',required=True)
	order_id = fields.Many2one(related='order_line_id.order_id',store=True)
	product_id = fields.Many2one(string='Producto',related='order_line_id.product_id',store=True)
	sale_uom_id = fields.Many2one(related='order_line_id.product_uom')
	type_calculator = fields.Selection([('common_product','Producto'),('service','Servicio')],string='Tipo de calculadora',required=True,default='common_product')

	total_area = fields.Float(string=u'Área total',digits=(10,4),compute='_compute_totals',store=True)
	total_sold_area = fields.Float(string='Área cobrada total',digits=(10,4),compute='_compute_totals',store=True)
	total_perimeter = fields.Float(string='Perímetro total',digits=(10,4),compute='_compute_totals',store=True)
	total_pieces = fields.Integer(string='Número de Piezas/Cristales',compute='_compute_totals',store=True)
	qty_invoiced = fields.Float('Cantidad Facturada',related='order_line_id.product_uom_qty')
	qty_invoiced_rest = fields.Float('Saldo por atender',digits=(10,4),compute='_compute_qty_invoiced_rest')
	line_ids = fields.One2many('glass.sale.calculator.line','calculator_id')


	@api.multi
	def write(self,values):
		if 'type_calculator' in values:
			self.line_ids.unlink() # si cambia de tipo de calculadora, borrar líneas anteriores
		return super(GlassSaleCalculator,self).write(values)
	
	### Constrains methods ###
	@api.constrains('total_sold_area','total_perimeter')
	def _verify_perimeter_sold_area(self):
		for rec in self:
			invoiced = rec.order_id.invoice_ids.filtered(lambda i: i.state!='cancel')
			if invoiced or rec.order_id.state!='draft' or rec.order_id.before_invoice:
				if rec.product_id.allow_metric_sale:
					magnitude = rec.total_perimeter
					msg = u'La suma de los perímetros ingresados supera al facturado'
				else:
					magnitude = rec.total_sold_area
					msg = u'La suma de las áreas ingresadas supera a la facturada'
				if magnitude > rec.qty_invoiced:
					raise ValidationError(msg)

	### Computed methods ###
	@api.depends('qty_invoiced','total_sold_area')
	def _compute_qty_invoiced_rest(self):
		for rec in self:
			rec.qty_invoiced_rest = rec.qty_invoiced - rec.total_sold_area

	@api.depends('line_ids.area','line_ids.perimeter','line_ids.sold_area','line_ids.quantity')
	def _compute_totals(self):
		for rec in self:
			lines = rec.line_ids
			rec.total_area = sum(lines.mapped('area'))
			rec.total_sold_area = sum(lines.mapped('sold_area'))
			rec.total_perimeter = sum(lines.mapped('perimeter'))
			rec.total_pieces = sum(lines.mapped('quantity'))

	def save_calculator(self):
		self.ensure_one()
		if not self.order_id.before_invoice:
			self.order_line_id.product_uom_qty = self.total_sold_area
		# recargar para actualizar visualmente
		action = self.env.ref('sale.action_quotations').read()[0]
		action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
		action['res_id'] = self.order_id.id
		return action

class GlassSaleCalculatorLine(models.Model):
	_name = 'glass.sale.calculator.line'

	calculator_id = fields.Many2one('glass.sale.calculator',ondelete='cascade')
	base1 = fields.Integer('Base 1 (mm)',required=True)
	base2 = fields.Integer('Base 2 (mm)',required=True)
	height1 = fields.Integer('Altura 1 (mm)',required=True)
	height2 = fields.Integer('Altura 2 (mm)',required=True)
	quantity = fields.Integer('Cantidad',required=True,default=0)
	crystal_num = fields.Char('Nro. de Cristales',required=1)
	descuadre = fields.Char('Descuadre',size=7)
	page_number = fields.Integer(u'Nro. Pág.')
	template = fields.Boolean('Plantilla')
	packed = fields.Boolean('Embalado')
	# entalle = fields.Integer('Entalle')
	# lavado = fields.Boolean('Lavado')
	# arenado = fields.Boolean('Arenado')
	# polished_id = fields.Many2one('sale.pulido.proforma',u'Pulido')
	image = fields.Binary('Imagen')
	measures = fields.Char('Medidas',compute='_compute_measures',readonly=True,store=True)
	perimeter = fields.Float(u"Perímetro",digits=(12,4),compute='_compute_perimeter',store=True)
	area = fields.Float(u'Área',digits=(10,4),compute='_compute_area',readonly=True,help=u'Área de los cristales calculada en M2.',store=True)
	sold_area = fields.Float(u'Área cobrada',digits=(10,4),compute='_compute_sold_area',help=u'Área de los cristales calculada en la unidad de medida de la línea de pedido de venta.',store=True)

	_sql_constraints = [
		('check_positive_base1','CHECK (base1>0)','La Base 1 debe ser mayor a cero.'),
		('check_positive_base2','CHECK (base2>0)','La Base 2 debe ser mayor a cero.'),
		('check_positive_height1','CHECK (height1>0)','La Altura 1 debe ser mayor a cero.'),
		('check_positive_height2','CHECK (height2>0)','La Altura 2 debe ser mayor a cero.'),
		('check_positive_quantity','CHECK (quantity>0)','La Cantidad debe ser mayor a cero.'),
	]

	@api.depends('base1','base2','height1','height2','quantity')
	def _compute_area(self):
		for rec in self:
			l1 = float(max([rec.base2,rec.base1]))
			l2 = float(max([rec.height1,rec.height2]))
			rec.area = round((l1*l2/1000000.0)*rec.quantity,4)

	@api.depends('area')
	def _compute_sold_area(self):
		for rec in self:
			area = rec.area
			sale_uom = rec.calculator_id.sale_uom_id
			prod_uom = rec.calculator_id.product_id.categ_id.uom_min_sale
			min_sale = rec.calculator_id.product_id.categ_id.min_sale
			
			value = prod_uom._compute_quantity(area,sale_uom)
			if min_sale > value:
				area = rec.quantity * prod_uom._compute_quantity(min_sale,sale_uom)
			rec.sold_area = area

	@api.depends('base1','base2','height1','height2','quantity')
	def _compute_perimeter(self):
		for rec in self:
			rec.perimeter = float(sum([rec.base1,rec.base2,rec.height1,rec.height2])*rec.quantity)/1000.0


	@api.depends('base1','base2','height1','height2')
	def _compute_measures(self):
		for rec in self:
			b1,b2,h1,h2,label = str(rec.base1),str(rec.base2),str(rec.height1),str(rec.height2),''
			if b1 == b2: label += b1
			else: label += b1 + '/' + b2
			label += 'X'
			if h1 == h2: label += h1
			else: label += h1 + '/' + h2
			rec.measures = label

	@api.constrains('crystal_num','quantity')
	def _check_crystal_num(self):
		for rec in self:
			validate = self.validate_crystal_number(rec.crystal_num,rec.quantity)
			if type(validate) in (str,unicode):
				raise ValidationError(validate)

	@api.constrains('descuadre')
	def _check_descuadre(self):
		for rec in self.filtered('descuadre'):
			validate = self.validate_descuadre(self.descuadre)
			if type(validate) in (str,unicode):
				raise ValidationError(validate)

	def validate_descuadre(self,string):
		self.ensure_one()
		if not re.match(r'^[1-4]+(,[1-4]+)*$',string,re.I):
			return u'El formato del descuadre es incorrecto, el patrón debe ser similar a 1,2 (con un máximo de 4 descuadres)\nValor ingresado: '+string
		
		dcd = string.split(',')
		duplicates = list(set([i for i in dcd if dcd.count(i)>1]))
		if any(duplicates):
			return u'Los siguientes valores se encuentran duplicados en el descuadre:\n%s\nValor ingresado: %s'%(' '.join(duplicates),string)

		h1=self.height1
		h2=self.height2
		b1=self.base1
		b2=self.base2
		data_line = u'¡No existe descuadre en el lado %d!\nDetalle de la línea:\nNro: %s\nAltura 1: %d\nAltura 2: %d\nBase 1: %d\nBase 2: %d'
		if '1' in dcd and b2==b1:
			return data_line%(1,self.crystal_num or '',h1,h2,b1,b2)
		if '3' in dcd and b2==b1:
			return data_line%(3,self.crystal_num or '',h1,h2,b1,b2)
		if '2' in dcd and h2==h1:
			return data_line%(2,self.crystal_num or '',h1,h2,b1,b2)
		if '4' in dcd and h2==h1:
			return data_line%(4,self.crystal_num or '',h1,h2,b1,b2)
		return True

	def validate_crystal_number(self,string,qty):
		regex1 = r'\b[0-9]{1,}-[0-9]{1,}\b' # validate format 3-5 23-56 ...
		#regex2 = r'^[0-9](,[0-9])*$' 		
		regex2 = r'^[0-9]+(,[0-9]+)*$'		# validate format 1,2,3,4,5...^[0-9]+(,[0-9]+)*$
		regex3 = r'^[0-9]+$'				# validate only numbers
		if qty==0:
			return u'La cantidad ingresada debe ser mayor a cero.'
		not_zero = lambda x: all([int(j) for j in x])
		if re.match(regex1,string,re.I):
			acadnro = string.split('-')
			if not not_zero(acadnro):
				return u"No es posible asignar cero a un número de cristal.\nValor ingresado: "+string
			if len(acadnro)>2:
				return u"Sólo puede ingresar un rango en el número de cristales (Ejemplo: 2-5)\nValor ingresado: "+string
			if int(acadnro[0])>int(acadnro[1]):
				return u"El rango de cristales debe comenzar con el número menor (Ejemplo: 2-5)\nValor Ingresado: "+string	
			init,end = int(acadnro[0]),int(acadnro[1])
			if (end-init+1) != qty:
				return u"El número de cristales debe corresponder a la cantidad indicada (%d):\nValor ingresado: %s"%(qty,string)
			return list(range(init,end+1))
		elif re.match(regex2,string,re.I) and ',' in string:
			acadnro = string.split(',')
			if not not_zero(acadnro):
				return u"No es posible asignar cero a un número de cristal.\nValor ingresado: "+string
			if len(acadnro) != qty:
				return u"El número de cristales debe corresponder a la cantidad indicada (%d)\nValor Ingresado: %s"%(qty,string)
			
			duplicates = list(set([i for i in acadnro if acadnro.count(i)>1]))
			if any(duplicates):
				return u'Los siguientes valores se encuentran duplicados en el número de cristales:\n%s\nValor ingresado: %s'%(' '.join(duplicates),string)
			return [int(n) for n in acadnro]
		elif re.match(regex3,string,re.I):
			if int(string) == 0:
				return u"No es posible asignar cero a un número de cristal.\nValor ingresado: "+string
			if qty>1:
				return u"El número de cristales debe corresponder a la cantidad indicada: "+str(qty)
			return [int(string)]
		else:
			return u'Error en formato de número de cristales!\nEl formato de número de cristal ingresado debe ser un número único, o en su defecto similar a 1-4 (rango de cristales) o una secuencia de números, similar a 1,2,3...\nValor Ingresado:'+string

	@api.onchange('crystal_num','quantity')
	def _onchange_crystal_num_quantity(self):
		res = {}
		if self.crystal_num and self.quantity:
			validate = self.validate_crystal_number(self.crystal_num,self.quantity)
			if type(validate) in (str,unicode):
				res['warning']={'title':u'Error en validación de número de cristales','message':validate}
		return res

	@api.onchange('descuadre')
	def _onchange_descuadre(self):
		res = {}
		if self.base1 and self.base2 and self.height1 and self.height2 and self.descuadre:
			validate = self.validate_descuadre(self.descuadre)
			if type(validate) in (str,unicode):
				res['warning']={'title':u'Error en validación de descuadre','message':validate}
		return res

	@api.onchange('base1','height1')
	def _onchange_base_height(self):
		if self.base2==0:
			self.base2 = self.base1
		if self.height2==0:
			self.height2 = self.height1

	@api.model
	def create(self,values):
		b1 = values['base1']
		b2 = values['base2']
		h1 = values['height1']
		h2 = values['height2']
		dcd = values.get('descuadre',[])
		values['image'] = self.draw_crystal(b1,b2,h1,h2,dcd)
		return super(GlassSaleCalculatorLine,self).create(values)

	@api.multi
	def write(self, values):
		image_depends = ('base1','base2','height1','height2','descuadre')
		for rec in self:
			if any([i for i in image_depends if i in values]):
				b1 = values.get('base1',rec.base1)
				b2 = values.get('base2',rec.base2)
				h1 = values.get('height1',rec.height1)
				h2 = values.get('height2',rec.height2)
				dcd = values.get('descuadre',(rec.descuadre or None))
				values['image'] = self.draw_crystal(b1,b2,h1,h2,dcd)
		return super(GlassSaleCalculatorLine,self).write(values)

	@api.multi
	def show_crystal_image(self):
		module = __name__.split('addons.')[1].split('.')[0]
		return {
			'name':'Imagen de Cristal',
			'res_id':self.id,
			'type': 'ir.actions.act_window',
			'res_model': self._name,
			'view_id': self.env.ref('%s.calculator_line_image_only_form'%module).id,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
			}

	@api.multi
	def back_view(self):
		module = __name__.split('addons.')[1].split('.')[0]
		module = self._context.get('module_name',module)
		values = self.calculator_id.order_line_id.with_context(module_name=module)._prepare_calculator_vals()
		return {
			'name':values['act_name'],
			'res_id': self.calculator_id.id,
			'type': 'ir.actions.act_window',
			'res_model': self.calculator_id._name,
			'view_id': self.env.ref(values['view']).id,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
			}

	def get_crystal_numbers(self):
		self.ensure_one()
		res = self.validate_crystal_number(self.crystal_num,self.quantity)
		if type(res) != list:
			raise UserError(res)
		return sorted(res)
		
	# @Params : base1:int base2:int height2:int height2:int dcd:descuadre -> text 
	# @return : encoded file to base64
	@api.model
	def draw_crystal(self,b1,b2,h1,h2,dcd=None,bg_color=(255,154,82)):
		size = [b1,b2,h1,h2]
		if not all(size):
			return False
		
		e_max = max(size)
		size = [x*500/e_max for x in size]
		
		w=850 # img width 
		h=650 # img height 
		image = Image.new("RGB",(w,h),color=(255,255,255))
		draw = ImageDraw.Draw(image)
		left= 170 
		top = 250 
		
		dcd = [int(x) for x in dcd.split(',')] if dcd else []

		p0 = (0.+left ,h/2+top)
		p1 = (0.+left, h/2-size[2]+top)
		p2 = (size[1]+left, h/2-size[3]+top)
		
		p3 = (size[0]+left, h/2-0.+top)
		p3_x = size[0]+left
		p3_y = h/2-0.+top

		if 1 in dcd:
			if b2>b1:
				p0 = ( p1[0]+(size[1]-size[0]),p0[1])
				p3_x = size[1]+left
			else:
				p1=(p1[0]+(size[0]-size[1]),p1[1])
				p2=(p3[0],p2[1])
		if 4 in dcd:
			if h2<h1:
				tmp=p1
				p1=(p0[0],p2[1])
				p3=(p3[0],p1[1]-(size[2]-size[3]))
				p3_y = p1[1]+(size[3]-(size[2]-size[3]))
			else:
				p2 = (size[1]+left, h/2-size[2]+top)
				p3_y = h/2-(size[2]-size[3])+top
		p3 = (p3_x,p3_y)
		points = (p0,p1,p2,p3,p0,)

		path = os.path.join(os.path.dirname(os.path.abspath(__file__)))+'/arial.ttf'
		font = ImageFont.truetype(path,36)
		
		maxheight = size[3] if p0[1]<p3[1] else size[2]
		maxwidth  = size[1] if size[0]<size[1] else size[0]
		moreleft  = p0[0] if p0[0]<p1[0] else p1[0]
		moreright = p3[0] if p2[0]<p3[0] else  p2[0]
		moretop   = p2[1] if p1[1]>p2[1] else p1[1]
		moreboot  = p3[1] if p0[1]<p3[1] else p0[1]

		draw.text((moreleft-155,(moreboot-(maxheight/2))), "LADO 1",font=font,fill=(255, 43, 0,128))
		draw.text((moreleft-155,((moreboot-(maxheight/2))+30)), str(h1)+" mm",font=font,fill=(51, 123, 164))
		
		draw.text((moreleft+((maxwidth/2)-120),moretop-80), "LADO 2",font=font,fill=(255, 43, 0,128))
		draw.text((moreleft+((maxwidth/2)-120),moretop-50), str(b2)+" mm",font=font,fill=(51, 123, 164))

		draw.text((moreright+20,(moreboot-(maxheight/2))), "LADO 3",font=font,fill=(255, 43, 0,128))
		draw.text((moreright+20,(moreboot-(maxheight/2))+30), str(h2)+" mm",font=font,fill=(51, 123, 164))

		draw.text((moreleft+((maxwidth/2)-120),moreboot+10), "LADO 4",font=font,fill=(255, 43, 0,128))
		draw.text((moreleft+((maxwidth/2)-120),moreboot+40), str(b1)+" mm",font=font,fill=(51, 123, 164))
		draw.polygon((points),fill=bg_color)

		for d in dcd:
			draw.line((points[d-1][0],points[d-1][1],points[d][0],points[d][1]),fill=(0,61,4),width=15)

		path = self.env['main.parameter'].search([])[0].dir_create_file+'glass.png'
		image.save(path)
		with open(path,'rb') as file:
			encoded_file = base64.b64encode(file.read())
		if os.path.exists(path):
			os.remove(path)
		return encoded_file