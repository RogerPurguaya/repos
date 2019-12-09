# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class MtfParameterConfig(models.Model):
	_name = 'mtf.parameter.config'

	name = fields.Char('Nombre',default=u"Parámetros de Fichas maestras")

	mat_prima_location_id = fields.Many2one('stock.location',string='Ubicación de Materia Prima',help=u'Ubicación que determinará si una línea de ficha maestra será materia prima')
	category_insulados_id = fields.Many2one('product.category',string='Categ. Insulados') # cristales insulados

	requisition_seq_id = fields.Many2one('ir.sequence',string='Secuencia para requisiciones')
	req_default_pick_type_id = fields.Many2one('stock.picking.type',string=u'Operación de Requisición por defecto')
	req_default_traslate_motive_id = fields.Many2one('einvoice.catalog.12',string=u'Motivo de traslado por defecto')
	#gastos_insumos_location_id = fields.Many2one('stock.location',string='Ubicación de Gastos Insumos',help=u'Ubicación que determinará si una línea de ficha maestra será un Gasto/Insumo')

	discount_categ_a = fields.Float(u'Descuento categoría A',default=0.0)
	discount_categ_b = fields.Float(u'Descuento categoría B',default=0.0)
	discount_categ_c = fields.Float(u'Descuento categoría C',default=0.0)
	discount_categ_d = fields.Float(u'Descuento categoría D',default=0.0)

	# Importante: los sufijos son usados en el template : cr_tmp,mt,cr_lam 
	# cristales templados
	manpower_cr_tmp = fields.Float('Mano de Obra Crist. Temp.',default=0.0)
	services_cr_tmp = fields.Float('Servicio de terceros Crist. Temp.',default=0.0)
	depreciacion_cr_tmp = fields.Float(u'Depreciación Crist. Temp.',default=0.0)
	cost_safe_cr_tmp = fields.Float('Seguros Crist. Temp.',default=0.0)
	tributes_cr_tmp = fields.Float('Tributos Crist. Temp.',default=0.0)
	cost_adm_sales_cr_tmp = fields.Float('Gastos Adm y Ventas Crist. Temp.',default=0.0)
	util_percent_cr_tmp = fields.Float('Margen sobre la venta Crist. Temp.',default=0.0)

	# Ficha maestra
	manpower_cr_ins = fields.Float('Mano de Obra Fichas Maestras',default=0.0)
	services_cr_ins = fields.Float('Servicio de terceros Fichas Maestras',default=0.0)
	depreciacion_cr_ins = fields.Float(u'Depreciación Fichas Maestras',default=0.0)
	cost_safe_cr_ins = fields.Float('Seguros Fichas Maestras',default=0.0)
	tributes_cr_ins = fields.Float('Tributos Fichas Maestras',default=0.0)
	cost_adm_sales_cr_ins = fields.Float('Gastos Adm y Ventas Fichas Maestras',default=0.0)
	util_percent_cr_ins = fields.Float('Margen sobre la venta Fichas Maestras',default=0.0)

	# Cristales laminados
	manpower_cr_lam = fields.Float('Mano de Obra Crist. Laminado',default=0.0)
	services_cr_lam = fields.Float('Servicio de terceros Crist. Laminado',default=0.0)
	depreciacion_cr_lam = fields.Float(u'Depreciación Crist. Laminado',default=0.0)
	cost_safe_cr_lam = fields.Float('Seguros Crist. Laminado',default=0.0)
	tributes_cr_lam = fields.Float('Tributos Crist. Laminado',default=0.0)
	cost_adm_sales_cr_lam = fields.Float('Gastos Adm y Ventas Crist. Laminado',default=0.0)
	util_percent_cr_lam = fields.Float('Margen sobre la venta Crist. Laminado',default=0.0)

	# Carpintería metálica
	manpower_carp_met = fields.Float('Mano de Obra Carp. metálica',default=0.0)
	services_carp_met = fields.Float('Servicio de terceros Carp. metálica',default=0.0)
	depreciacion_carp_met = fields.Float(u'Depreciación Carp. metálica',default=0.0)
	cost_safe_carp_met = fields.Float('Seguros Carp. metálica',default=0.0)
	tributes_carp_met = fields.Float('Tributos Carp. metálica',default=0.0)
	cost_adm_sales_carp_met = fields.Float('Gastos Adm y Ventas Carp. metálica',default=0.0)
	util_percent_carp_met = fields.Float('Margen sobre la venta Carp. metálica',default=0.0)

	# Pegado de Silicona
	manpower_peg_sil = fields.Float('Mano de Obra Peg. de Silicona',default=0.0)
	services_peg_sil = fields.Float('Servicio de terceros Peg. de Silicona',default=0.0)
	depreciacion_peg_sil = fields.Float(u'Depreciación Peg. de Silicona',default=0.0)
	cost_safe_peg_sil = fields.Float('Seguros Peg. de Silicona',default=0.0)
	tributes_peg_sil = fields.Float('Tributos Peg. de Silicona',default=0.0)
	cost_adm_sales_peg_sil = fields.Float('Gastos Adm y Ventas Peg. de Silicona',default=0.0)
	util_percent_peg_sil = fields.Float('Margen sobre la venta Peg. de Silicona',default=0.0)

	# Armado de paneles (pendiente)
	# manpower_arm_pan = fields.Float('Mano de Obra Arm. de paneles',default=0.0)
	# services_arm_pan = fields.Float('Servicio de terceros Arm. de paneles',default=0.0)
	# depreciacion_arm_pan = fields.Float(u'Depreciación Arm. de paneles',default=0.0)
	# cost_safe_arm_pan = fields.Float('Seguros Arm. de paneles',default=0.0)
	# tributes_arm_pan = fields.Float('Tributos Arm. de paneles',default=0.0)
	# cost_adm_sales_arm_pan = fields.Float('Gastos Adm y Ventas Arm. de paneles',default=0.0)
	# util_percent_arm_pan = fields.Float('Margen sobre la venta Arm. de paneles',default=0.0)

	_sql_constraints = [('check_discounts','CHECK (discount_categ_a>=0 and discount_categ_a<=100 and discount_categ_b>=0 and discount_categ_b<=100 and discount_categ_c>=0 and discount_categ_c<=100 and discount_categ_d>=0 and discount_categ_d<=100)',u'Los porcentajes de descuento deben estar en el rango de 0 a 100.')]

	@api.model
	def create(self, values):
		if self.search_count([]) != 0:
			raise UserError(u'Ya existe un registro de parámetros de configuración')
		return super(MtfParameterConfig,self).create(values)

	@api.multi
	def unlink(self):
		if self.env['mtf.template'].search_count([('config_id','=',self.id)]) > 0:
			raise UserError(u'No es posible eliminar los parámetros de configuración de debido a que hay fichas maestras que los utilizan')
		return super(MtfParameterConfig,self).unlink()