# -*- encoding: utf-8 -*-
{
	'name': 'Ordenes de produccion Glass ',
	'category': 'production',
	'author': 'ITGRUPO-POLIGLASS',
	'depends': [
		'sale_calculadora_it',
		'kardex_it',
		'kardex_product_saldofisico_it',
		'unidad_medida_it',
		'stock',
		'custom_glass_locations',
		'config_payment_terms_fullglass',
		'sales_team',
	],
	'version':'1',
	'description':"""
		Ordenes de produccion Glass
		install poppler 
		Windows https://blog.alivate.com.au/poppler-windows/ and add bin folder to path
		In linux: apt-get install poppler
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/groups.xml',
		'security/ir.model.access.csv',
		'data/data.xml',
		'views/glass_order_view.xml',
		'views/glass_order_config_view.xml',
		'views/glass_lot_view.xml',
		'views/sale_order_view.xml',
		'views/glass_tracing_production_stock_view.xml',
		'views/glass_requisition_view.xml',
		'views/product_uom_view.xml',
		'views/purchase_requisition_view.xml',
		'views/glass_furnace_out_view.xml',
		'views/stock_move_view.xml',
		'views/glass_tracing_production_view.xml',
		'views/requisition_material_view.xml',
		'views/glass_send_emails_config.xml',
		'views/requisition_workers.xml',
		'views/glass_scrap.xml',
		'views/glass_sale_calculator.xml',
		'report/glass_barcode_report.xml',
		'wizard/views_wizards/glass_in_production_wizard.xml',
		'wizard/views_wizards/glass_make_uom_view.xml',
		'wizard/views_wizards/glass_in_stock_picking_show_details_wizard.xml',
		'wizard/views_wizards/show_detail_lines_entered_stock_wizard_view.xml',
		'wizard/views_wizards/show_detail_tracing_line_view.xml',
		'wizard/views_wizards/add_sketch_file_view.xml',
		'wizard/views_wizards/glass_remove_order_view.xml',
		'wizard/views_wizards/glass_pool_wizard_view.xml',
		'wizard/views_wizards/glass_croquis_sale_wizard_view.xml',
		'wizard/views_wizards/build_glass_order_wizard.xml',
		'wizard/views_wizards/glass_production_control_wizard_view.xml',
        ],
    'css': [
		'static/src/css/sheet.css'
		],
	'installable': True
}