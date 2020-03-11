# -*- encoding: utf-8 -*-
{
	'name': 'Kardex Account Reports Comparation',
	'version': '1.0',
	'author': 'ITGRUPO',
	'website': '',
	'category': 'account',
	'depends': ['kardex_it','account_diario_it'],
	'description': """Reporte de facturas inexistentes en contabilidad pero existentes en Kardex""",
	'demo': [],
	'data': [
		'kardex_account_report.xml',
		'export_file.xml'
	],
	'auto_install': False,
	'installable': True
}
