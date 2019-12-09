# -*- coding: utf-8 -*-
{
	'name': "Logística de Insulados - Fullglass",

	'summary': """
		Gestión de la logística de cristales insulados
		""",

	'description': """
		- Encargado de gestionar el envío de cristales base para su Insulación.
		- Encargado de adicionar la etapa de marcar la etapa de insulado a los cristales solicitados con estas características. 
	""",

	'author': "ITGRUPO-POLIGLASS",
	'website': "http://www.itgrupo.net",

	'category': 'Sale-Production',
	'version': '0.1',

	# any module necessary for this one to work correctly
	'depends': ['base','master_template_fullglass'],

	# always loaded
	'data': [
		'security/groups.xml',
		'security/ir.model.access.csv',
		#'data/data.xml',
		#'views/sale_order.xml',
		#'views/mtf_template.xml',
		#'views/glass_sale_calculator.xml',
		#'views/glass_sale_calculator_line.xml',
		#'views/glass_order.xml',
		#'views/glass_lot.xml',
		#'views/mtf_parameter_config.xml',
		#'views/mtf_requisition.xml',
		#'wizard/mtf_confirm_update_template.xml',
		'wizard/finish_insulados_wizard.xml',
	],
	'demo': [],
	'installable': True
}