# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import re

class GlassStage(models.Model):
	_name = 'glass.stage'
	_description = u'Etapa/Proceso de cristal'

	name = fields.Char('Nombre',required=True,index=True)
	description = fields.Text(u'Descripción')

	_sql_constraints = [('uniq_name','UNIQUE (name)',u'El nombre de la etapa debe ser único')]

	@api.constrains('name')
	def _verify_name(self):
		for stage in self:
			if not re.match(r'^[a-z0-9_]*$',stage.name):
				raise ValidationError(u'El nombre de etapa debe contener sólo caracteres alfanuméricos y en minúscula, además no debe tener espacios.')