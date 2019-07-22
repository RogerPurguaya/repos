# -*- encoding: utf-8 -*-
{
	'name': 'Actualizar Toponimos Actualizados',
	'category': 'account',
	'author': 'ITGRUPO-POWER-TEST',
	'depends': ['partner_ruc_wsdl_it','partner_dni_wsdl_it','stock','sales_team'],
	'version': '1.0',
	'description':"""
	Actualizar todos los Toponimos Actualizados
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
	'actualizar_toponimos_wizard.xml',
	],
	'installable': True
}