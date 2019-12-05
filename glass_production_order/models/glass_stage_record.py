# -*- coding: utf-8 -*-
from odoo import fields, models,api, _

# class GlassStageRecord(models.Model):
# 	_name='glass.stage.record'

# 	user_id = fields.Many2one('res.users','Usuario')
# 	date = fields.Date('Fecha')
# 	time = fields.Char('Hora')
# 	stage = fields.Selection([
# 		('optimizado','Optimizado'),
# 		('requisicion',u'Requisición'),
# 		('corte','Corte'),
# 		('pulido','Pulido'),
# 		('entalle','Entalle'),
# 		('lavado','Lavado'),
# 		('horno','Horno'),
# 		('templado','Templado'),
# 		('compra','Comprado'),
# 		('entregado','Entregado'),
# 		('ingresado','Ingresado'),
# 		('roto','Rotura'),
# 		('retirado','Retirado'),
# 		],'Etapa')
# 	lot_line_id  =  fields.Many2one('glass.lot.line',u'Línea de lote')
# 	break_motive = fields.Char('Motivo de rotura')
# 	break_stage  = fields.Char('Etapa de Rotura')
# 	break_note   = fields.Text(u'Observación de Rotura')
# 	date_fisical = fields.Date() 
	# campo en desuso (no tomarlo en cuenta)

class GlassStageRecord(models.Model):
	_name='glass.stage.record'

	user_id = fields.Many2one('res.users',u'Usuario responsable',required=True)
	stage_id = fields.Many2one('glass.stage',string=u'Etapa',ondelete='restrict')
	lot_line_id  =  fields.Many2one('glass.lot.line',u'Línea de lote',required=True,ondelete='cascade')
	date = fields.Datetime('Fecha y hora de registro',required=True)
	done = fields.Boolean('Realizado')

	# solo para registrar detalles en caso sea rotura
	break_motive = fields.Char('Motivo de rotura')
	break_stage_id = fields.Many2one('glass.stage',string=u'Etapa de rotura')
	break_note   = fields.Text(u'Observación de Rotura')

	#date = fields.Date('Fecha')
	#time = fields.Char('Hora')
	# stage = fields.Selection([
	# 	('optimizado','Optimizado'),
	# 	('requisicion',u'Requisición'),
	# 	('corte','Corte'),
	# 	('pulido','Pulido'),
	# 	('entalle','Entalle'),
	# 	('lavado','Lavado'),
	# 	('horno','Horno'),
	# 	('templado','Templado'),
	# 	('compra','Comprado'),
	# 	('entregado','Entregado'),
	# 	('ingresado','Ingresado'),
	# 	('roto','Rotura'),
	# 	('retirado','Retirado'),
	# 	],'Etapa')
	#date_fisical = fields.Date() 