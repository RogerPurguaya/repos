# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class GlassOrderConfig(models.Model):
	_inherit = 'glass.order.config'

	pick_type_out_ins_id = fields.Many2one('stock.picking.type',string='Tipo de picking sal. Insulados',help=u'Tipo de picking para salida de cristales para insulado a planta de insulación')
	
	pick_type_in_ins_id = fields.Many2one('stock.picking.type',string='Tipo de picking sal. Insulados',help=u'Tipo de picking para Ingreso de producto terminado Insulado')