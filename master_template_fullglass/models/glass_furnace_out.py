# -*- coding: utf-8 -*-
from odoo import fields, models,api,exceptions, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta

class GlassFurnaceOut(models.Model):
	_inherit='glass.furnace.out'

	def _register_info(self,line):
		if line.from_insulado:
			line.with_context(force_register=True).register_stage('templado')
			line.is_used=True #??
			#line.order_line_id.state = 'ended' # esta vaina debería setearse al marcar como "producido"
		else:
			super(GlassFurnaceOut,self)._register_info(line)