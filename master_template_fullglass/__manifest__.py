# -*- coding: utf-8 -*-
{
	'name': "Plantillas maestras - Fullglass",

	'summary': """
		Fichas maestras para el cálculo de costos en cristales insulados,templados,etc.
		""",

	'description': """
		Módulo de fichas maestras en para la corporación FullGlass
	""",

	'author': "ITGRUPO-POLIGLASS",
	'website': "http://www.itgrupo.net",

	'category': 'Sale-Production',
	'version': '0.1',

	# any module necessary for this one to work correctly
	'depends': ['base','glass_production_order','sales_team'],

	# always loaded
	'data': [
		'security/groups.xml',
		'security/ir.model.access.csv',
		'data/data.xml',
		'views/sale_order.xml',
		'views/mtf_template.xml',
		'views/glass_sale_calculator.xml',
		'views/glass_sale_calculator_line.xml',
		'views/glass_order.xml',
		'views/mtf_parameter_config.xml',
		'wizard/mtf_confirm_update_template.xml',
		'wizard/mtf_req_material_pool_wizard.xml',
	],
	'demo': [],
	'css':[
		'static/src/css/sheet.css',
	],
	'installable': True
}