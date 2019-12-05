# -*- coding: utf-8 -*-
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare
from odoo.exceptions import UserError,ValidationError

class MasterTemplate(models.Model):
	_name = 'mtf.template'
	
	# campos del product:
	# product_id = fields.Many2one('product.product',ondelete='restrict',required=True,
	# 	domain=lambda self: [('categ_id','=',self.env['glass.order.config'].search([],limit=1).category_insulados_id.id)],
	# 	string='Producto Insulado',copy=False)
	product_id = fields.Many2one('product.product',ondelete='restrict',string='Producto',copy=False)
	code = fields.Char(u'Código de producto',related='product_id.default_code')
	measure = fields.Float('Medida')
	uom_id = fields.Many2one(related='product_id.uom_id',string='Unidad')
	weight = fields.Float('Peso',related='product_id.weight')
	quantity = fields.Float('Cantidad',default=1.0)
	stock = fields.Float('Stock')
	int_code = fields.Char(u'Código Internacional')

	def _get_default_config(self):
		try:
			config = self.env['mtf.parameter.config'].search([],limit=1)[0]
		except IndexError:
			raise UserError(u'No se han encontrado los parámetros de configuración para Fichas Maestras')
		return config.id

	config_id = fields.Many2one('mtf.parameter.config',string='Config',default=_get_default_config)
	mat_prima_location_id = fields.Many2one(related='config_id.mat_prima_location_id')

	# definir esta mrd...
	# cr_tmp -> Cristal templado
	# cr_ins -> Cristal Insulado
	# cr_lam -> Cristal Insulado
	# carp_met -> Carpintería metálica
	# peg_sil -> Pegado de Silicona
	# arm_pan -> Armado de paneles
	applied_on = fields.Selection([('cr_tmp','Cristal Templado'),('cr_ins','Cristal Insulado'),('cr_lam','Cristal Laminado'),('carp_met',u'Carpintería metálica'),('peg_sil','Pegado de Silicona')],string='Aplicación de Ficha',default='cr_tmp')
	cost_mp = fields.Float('Costo Materia Prima')
	cost_insumos = fields.Float('Gastos insumos rep. y sum.')
	amount_total = fields.Float('Total Costo Materiales') #
	area_total   = fields.Float(u'Area Total',digits=(10,4))
	manpower = fields.Float('Mano de Obra',default=0.0)
	services = fields.Float('Servicios',default=0.0)
	depreciacion = fields.Float(u'Depreciación',default=0.0)
	cost_safe = fields.Float(u'Seguros',default=0.0)
	tributes = fields.Float(u'Tributos',default=0.0)
	
	total_indirect_costs = fields.Float('Total indirectos de Fabricación',default=0.0)
	total_cost_manufacturing = fields.Float('Costo total de Fabricación',default=0.0)
	cost_adm_sales = fields.Float('Gastos Adm. y ventas',default=0.0)
	total_cost = fields.Float('Costo total',default=0.0)

	util_percent = fields.Float('Margen de ganancia(%)',default=35.00)
	sale_price  = fields.Float('Precio de Venta',default=0.0)
	
	# Modelos/Precios esta vaina la dejaré comentada por siaca
	#qty_unit_costed = fields.Float('Unidades costeadas',default=1.0,help=u'Unidades que se costean.')
	#currency_id = fields.Many2one('res.currency',string='Moneda')
	#net_price_avg = fields.Float('Precio Neto Promedio')
	#flete_amount = fields.Float('Flete',default=0.0)
	#uom_price = fields.Float('Precio',default=0.0,help=u'Precio de "Unidades costeadas" en la unidad incluyendo el flete.')
	#min_qty_sale = fields.Float('Venta min',default=0.0,help=u'Venta mínima de éste producto')

	# campos solo referanciales , no utilizar para otras cosas 
	margin_obj = fields.Float('Margen Obj.')
	currency_id = fields.Many2one('res.currency',string='Moneda',default=lambda self: self.env.user.company_id.currency_id.id)
	discount_a = fields.Float(related='config_id.discount_categ_a',string='Descuento A (%)')
	discount_b = fields.Float(related='config_id.discount_categ_b',string='Descuento B (%)')
	discount_c = fields.Float(related='config_id.discount_categ_c',string='Descuento C (%)')
	discount_d = fields.Float(related='config_id.discount_categ_d',string='Descuento D (%)')
	
	ref_product_id = fields.Many2one(related='product_id')
	ref_uom_id = fields.Many2one(related='uom_id')
	ref_total_cost = fields.Float(related='total_cost')
	ref_util_percent = fields.Float(related='util_percent')
	ref_sale_price = fields.Float(related='sale_price')

	line_ids = fields.One2many('mtf.template.line','template_id',string='Detalle',copy=True)
	stage_ids=fields.Many2many('glass.stage','mtf_template_glass_rel','template_id','stage_id',string='Procesos')

	# registra etapas sólo para el cristal de insulado 1
	ins_cr_1_stage_ids=fields.Many2many('glass.stage','mtf_template_stage_cr1_rel','template_id','stage_id',string='Procesos Ins. Cristal 1')
	# registra etapas sólo para el cristal de insulado 2
	ins_cr_2_stage_ids=fields.Many2many('glass.stage','mtf_template_stage_cr2_rel','template_id','stage_id',string='Procesos Ins. Cristal 2')

	active = fields.Boolean('Activo',default=True)

	# Minimos 
	min_base   = fields.Integer(default=0)
	min_height = fields.Integer(default=0)
	min_movil  = fields.Integer(default=0)
	min_sobre  = fields.Integer(default=0)
	min_alfe   = fields.Integer(default=0)
	# standard
	std_base   = fields.Integer(default=0)
	std_height = fields.Integer(default=0)
	std_movil  = fields.Integer(default=0)
	std_sobre  = fields.Integer(default=0)
	std_alfe   = fields.Integer(default=0)
	# maximos
	max_base   = fields.Integer(default=0)
	max_height = fields.Integer(default=0)
	max_movil  = fields.Integer(default=0)
	max_sobre  = fields.Integer(default=0)
	max_alfe   = fields.Integer(default=0)

	_sql_constraints = [(
	'check_measures','CHECK ((max_base>=std_base and std_base>=min_base and min_base>=0) and (max_height>=std_height and std_height>=min_height and min_height>=0) and (max_movil>=std_movil and std_movil>=min_movil and min_movil>=0) and (max_sobre>=std_sobre and std_sobre>=min_sobre and min_sobre>=0) and (max_alfe>=std_alfe and std_alfe>=min_alfe and min_alfe>=0))',u'Las medidas mínimas, standard y máximas deben corresponder a su definición (Longitudes máximas superiores a standard y longitudes standard supreriores a mínimas) y todas deben ser mayores o iguales a cero.')]

	_rec_name = 'product_id'

	@api.constrains('product_id')
	def _verify_constrains_product_id(self):
		ins_categ = self.config_id.category_insulados_id
		for rec in self:
			if self.search_count([('product_id','=',rec.product_id.id)]) > 1:
				raise ValidationError(u'El producto %s ya fue asignado a una ficha maestra de cristales insulados.'%rec.product_id.name)
			if rec.product_id.categ_id != ins_categ and rec.applied_on=='cr_ins':
				raise ValidationError(u'El producto %s no corresponde a la categoría de cristales insulados configurada.'%rec.product_id.name)

	# verificar que si es insulado, debe tener 2 cristales de insulados
	@api.constrains('line_ids','applied_on')
	def _verify_line_ids(self):
		for rec in self:
			if rec.applied_on=='cr_ins': # en insulados deben haber por lo menos 2 cristales
				crystal_lines = rec.line_ids.filtered('pos_ins_crystal')
				if len(crystal_lines) not in (2,3): # min 2 max 3 cristales
					raise ValidationError(u'Debe especificar como mínimo 2 cristales en su lista de materiales para cristales insulados.')

	def compute_template(self):
		# Process total lines:
		self.ensure_one()
		ctx = self._context
		not_costed_lines = ctx.get('not_costed_lines',[]) # si no se costea desde calculadora
		lines = self.line_ids.filtered(lambda l: not l.not_costed and l.id not in not_costed_lines)
		line_vals = dict.fromkeys(lines.ids)

		base_in = ctx.get('base',self.std_base)
		height_in = ctx.get('height',self.std_height)

		if base_in > self.max_base or base_in < self.min_base:
			raise UserError('La base ingresada debe estar entre los rangos de %d a %d'%(self.min_base,self.max_base))
		if height_in > self.max_height or height_in < self.min_height:
			raise UserError('La altura ingresada debe estar entre los rangos de %d a %d'%(self.min_height,self.max_height))

		for line in lines:
			line_vals[line.id] = line._compute_line(base_in,height_in)

		values = line_vals.values()
		mp,insumos = [],[]
		for val in values:
			if val['raw_material']:
				mp.append(val['amount_untaxed'])
			else:
				insumos.append(val['amount_untaxed'])

		area = filter(lambda i: i['base'] and i['height'] and not i['fixed'],values)
		area_total = sum(map(lambda x: float(x['base']*x['height'])/1000000.0,area))
		
		cost_mp = sum(mp)
		cost_insumos = sum(insumos)
		amount_total = cost_mp + cost_insumos
		app_on = self.applied_on
		manpower     = (getattr(self.config_id,'manpower_'+app_on)) * area_total
		services     = (getattr(self.config_id,'services_'+app_on)) * area_total
		depreciacion = (getattr(self.config_id,'depreciacion_'+app_on)) * area_total
		cost_safe    = (getattr(self.config_id,'cost_safe_'+app_on)) * area_total
		tributes     = (getattr(self.config_id,'tributes_'+app_on)) * area_total
		cost_adm_sales = (getattr(self.config_id,'cost_adm_sales_'+app_on)) * area_total
		util_percent = (getattr(self.config_id,'util_percent_'+app_on)) * area_total

		total_indirect_costs = manpower + services + depreciacion + cost_safe + tributes
		total_cost_manufacturing = total_indirect_costs + amount_total
		total_cost = total_cost_manufacturing + cost_adm_sales
		sale_price = total_cost/(1-(util_percent/100)) # pendiente de validación
		#sale_price = total_cost*(1+(util_percent/100)) # al parecer es esto xD

		if ctx.get('only_sale_price'):
			return sale_price
		elif ctx.get('all_line_values'):
			return sale_price,line_vals
		vals = {
			'cost_mp':cost_mp,
			'cost_insumos':cost_insumos,
			'amount_total':amount_total,
			'manpower':manpower,
			'services':services,
			'depreciacion':depreciacion,
			'cost_safe':cost_safe,
			'tributes':tributes,
			'cost_adm_sales':cost_adm_sales,
			'util_percent':util_percent,
			'total_indirect_costs':total_indirect_costs,
			'total_cost_manufacturing':total_cost_manufacturing,
			'total_cost':total_cost,
			'sale_price':sale_price,
			'area_total':area_total,
			'line_ids':[(1,k,v) for k,v in line_vals.items()]
		}
		if float_compare(sale_price,self.sale_price,precision_digits=2)!=0:
			module = __name__.split('addons.')[1].split('.')[0]
			wiz = self.env['mtf.confirm.update.template'].create({
				'template_id':self.id,
				'current_sale_price':self.sale_price,
				'new_sale_price':sale_price,
				})
			return {
				'name':'Confirmar actualización de Ficha Maestra',
				'res_id':wiz.id,
				'type': 'ir.actions.act_window',
				'res_model': wiz._name,
				'view_id': self.env.ref('%s.mtf_confirm_update_template_view_form'%module).id,
				'view_mode': 'form',
				'view_type': 'form',
				'target': 'new',
				'context':{'vals':vals}
				}
		self.write(vals)

	def update_process_lines(self):
		line_ids = self.line_ids.ids
		to_remove = self.line_process_ids.filtered(lambda x: x.template_line_id.id not in line_ids)
		to_remove.unlink()
		existing = self.line_process_ids.mapped('template_line_id').ids
		new_values = [(0,0,{'template_line_id':l}) for l in line_ids if l not in existing]
		if any(new_values):
			self.line_process_ids = new_values


class MasterTemplateLine(models.Model):
	_name = 'mtf.template.line'

	template_id  = fields.Many2one('mtf.template',ondelete='cascade')
	pos_ins_crystal = fields.Selection([(1,'Cristal 1'),(2,'Cristal 2'),(3,'Cristal 3')],help=u'Posición en cristal insulado',string='Posición cristal')
	to_produce = fields.Boolean(u'Producción',help="Determina si el cristal debe ser producido")
	not_costed = fields.Boolean('No Costeado',help=u'Destermina el ésta línea de ficha será costeada o no') 
	product_id = fields.Many2one('product.product',string='Producto')
	default_code = fields.Char(related='product_id.default_code')
	model  = fields.Char(string='Modelo',compute='_compute_model')
	uom_id = fields.Many2one(related='product_id.uom_id', string='Unidad')
	unit_price   = fields.Float('Precio Unitario',digits=dp.get_precision('Product Price'),default=0.0)
	un_price_special = fields.Float('Precio Unitario Mat. propio',digits=dp.get_precision('Product Price'),default=0.0,help=u'Costo unitario si el material es propiedad del cliente')
	uom_quantity = fields.Float('Cantidad',default=0.0)
	fixed  = fields.Boolean('Fijo')
	base   = fields.Integer(string='Base')
	inc_b = fields.Integer('IncB',default=0,help=u'Descuento en la medida de la base.')
	height = fields.Integer(string='Altura')
	inc_h = fields.Integer('IncA',default=0,help=u'Descuento en la medida de la altura.')
	depending_on = fields.Selection(string=u'En función de', selection=[('b', 'Base'),('h','Altura'),('bxh', 'Base x Altura'),('p',u'Perímetro'),('vxp',u'Volumen x Perímetro')])
	location = fields.Selection(string='Ubicación', selection=[('marco', 'Marco'), ('hoja_fija', 'Hoja Fija'),('hoja_movil',u'Hoja Móvil'),('sobreluz','Sobreluz'),('alteizar','Alteizar'),('cristal','Cristal')])
	position = fields.Selection(string='Posición', selection=[('left', 'Izquierda'), ('right', 'Derecha'),('t_horizontal',u'Travesaño Horizontal'),('t_verical',u'Travesaño Vertical'),('top_bottom','Arriba/Abajo'),('left_right','Izquierda/Derecha'),('4_sides','Cuatro Lados')])
	cut = fields.Char('Corte') # free text
	raw_material = fields.Boolean('Es materia Prima')
	cut_type = fields.Selection(string='Tipo', selection=[('revestimiento','Material de Revestimiento'),('accesorios_panel','Accesorios para Panel'),('instalacion_insumos',u'Insumos de Instalación'),('mano_obra','Mano de Obra'),('instalacion_equipos',u'Equipos de Instalación'),('servicios_terceros','Servicios de Terceros'),('insumos_proceso','Insumos con proceso')])
	waste_percent= fields.Float('% Merma',default=0.0)

	# es producto spacer
	is_spacer = fields.Boolean('Separador')
	application = fields.Char('Aplicación') # free text
	total_units    = fields.Float('Total Unidades',digits=(12,4),default=0.0)
	amount_untaxed = fields.Float('Total Costo sin IGV',digits=(12,4),default=0.0)

	# si es fijo va en función a nada
	@api.onchange('fixed')
	def _onchange_fixed(self):
		if self.fixed: self.depending_on = False
			
	@api.onchange('product_id')
	def _onchange_product_id(self):
		self.unit_price = self.product_id.standard_price # por mientras

	@api.onchange('depending_on')
	def _onchange_depending_on(self):
		if self.depending_on:
			self.base = self.template_id.std_base or 0
			self.height = self.template_id.std_height or 0

	@api.constrains('base','height','depending_on')
	def _verify_base_height(self):
		for rec in self:
			if rec.depending_on and (not rec.base or not rec.height):
				raise ValidationError(u'Error de validación!\nCuando agrega una línea en función de alguna dimensión (perímetro,base por altura, etc) debe asignar una base y una altura a dicha línea.')
			if not rec.depending_on and (rec.base or rec.height):
				raise ValidationError(u'Error de validación!\nUd agregó una base y/o altura a una línea que no depende de dichas dimensiones.\nQuite dichos valores para poder continuar.')

	@api.one
	@api.depends('product_id')
	def _compute_model(self):
		attr = self.product_id.atributo_ids.filtered(lambda x: x.atributo_id.id==4)
		self.model = attr[0].valor_id.name if any(attr) else ''

	def _compute_line(self,base,height):
		self.ensure_one()
		total_units = 0.0
		depending_on = self.depending_on
		base = (base-self.inc_b) if depending_on else False
		height = (height-self.inc_h) if depending_on else False
		if self.fixed:
			total_units = self.uom_quantity
		elif depending_on=='bxh' and base and height:
			total_units = float(base*height)/1000000.0 * self.uom_quantity
		elif depending_on=='b' and base:
			total_units = float(base)/1000.0 * self.uom_quantity
		elif depending_on=='h' and height:
			total_units = float(height)/1000.0 * self.uom_quantity
		elif depending_on=='p' and base and height:
			total_units = float(base*2+height*2)/1000.0 * self.uom_quantity
		elif depending_on=='vxp' and base and height:
			spacer=self.template_id.line_ids.filtered(lambda x: x.is_spacer and x.model and not x.not_costed)
			if spacer:
				spacer = spacer[0]
				try:
					separator = float(''.join([i for i in spacer.model if i.isnumeric()]))
				except TypeError:
					separator = 0.0
			total_units = separator * self.inc_b * float(base*2+height*2)/1000.0 * self.uom_quantity
		
		# tmp merma le agrego al total de unidades la cantidad de merma o desperdicio:
		#total_units = total_units*(1+(self.waste_percent/100))
		total_units = total_units/(1-(self.waste_percent/100)) # revisar esta vaina
		mp_loc = self.template_id.config_id.mat_prima_location_id
		# por ahora todo lo q no esta en materia primas va a gastos e insumos
		#ig_loc = config.gastos_insumos_location_id 
		if not mp_loc:
			raise UserError(u'No se ha encontrado la configuración para las ubicaciones de productos de Ficha Maestra.')
		return {
			'product_id':self.product_id.id,
			'base': base,
			'height':height,
			'fixed': self.fixed,
			'total_units': total_units,
			'amount_untaxed': (total_units * self.unit_price)/1.18,
			'pos_ins_crystal':self.pos_ins_crystal,
			'to_produce':self.to_produce,
			'raw_material':bool(self.product_id.property_stock_inventory==mp_loc)
		}


