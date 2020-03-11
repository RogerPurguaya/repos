# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import odoo.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from odoo import models, fields, api
import codecs
from odoo.exceptions import UserError

class MakeKardexAccountWizard(models.TransientModel):
	_name = "make.kardex.acount.wizard"

	period_id = fields.Many2one('account.period','Periodo')
	fini= fields.Date('Fecha inicial',required=True)
	ffin= fields.Date('Fecha final',required=True)
	products_ids=fields.Many2many('product.product','rel_wiz_kardex_comparation','product_id','kardex_id')
	location_ids=fields.Many2many('stock.location','rel_kardex_location_comparation','location_id','kardex_id','Ubicacion',required=True)
	allproducts=fields.Boolean('Todos los productos',default=True)
	destino = fields.Selection([('csv','CSV'),('crt','Pantalla')],'Destino')
	check_fecha = fields.Boolean('Editar Fecha')
	alllocations = fields.Boolean('Todos los almacenes',default=True)
	fecha_ini_mod = fields.Date('Fecha Inicial')
	fecha_fin_mod = fields.Date('Fecha Final')
	analizador = fields.Boolean('Analizador',compute="get_analizador")

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	account_kardex = fields.Boolean(string='Contabilidad vs Kardex',default=False)
	is_resume = fields.Boolean(string='Es Resumen',default=False)

	@api.onchange('period_ini','period_end')
	def _change_periodo_ini(self):
		fiscalyear = self.env['main.parameter'].search([])[0].fiscalyear
		year = self.env['account.fiscalyear'].search([('name','=',fiscalyear)],limit=1)
		if not year:
			raise UserError(u'No se encontró el año fiscal configurado en parametros, utilice un año que exista actualmente')
		if fiscalyear == 0:
			raise UserError(u'No se ha configurado un año fiscal en Contabilidad/Configuracion/Parametros/')
		else:
			return {'domain':{'period_ini':[('fiscalyear_id','=',year.id )],'period_end':[('fiscalyear_id','=',year.id )]}}

	@api.multi
	def get_analizador(self):
		if 'tipo' in self.env.context:
			if self.env.context['tipo'] == 'valorado':
				self.analizador = True
			else:
				self.analizador = False
		else:
			self.analizador = False

	_defaults={
		'destino':'crt',
		'check_fecha': False,
		'allproducts': True,
		'alllocations': True,
	}

	@api.onchange('fecha_ini_mod')
	def onchange_fecha_ini_mod(self):
		self.fini = self.fecha_ini_mod

	@api.onchange('fecha_fin_mod')
	def onchange_fecha_fin_mod(self):
		self.ffin = self.fecha_fin_mod

	@api.model
	def default_get(self, fields):
		res = super(MakeKardexAccountWizard, self).default_get(fields)
		import datetime
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'
		res.update({'fecha_ini_mod':fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha_inicial})
		res.update({'ffin':fecha_hoy})

		#locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = [elemt.id for elemt in locat_ids]
		res.update({'location_ids':[(6,0,locat_ids)]})
		return res

	@api.onchange('alllocations')
	def onchange_alllocations(self):
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			self.location_ids = [(6,0,locat_ids.ids)]
		else:
			self.location_ids = [(6,0,[])]

	@api.onchange('period_id')
	def onchange_period_id(self):
		self.fini = self.period_id.date_start
		self.ffin = self.period_id.date_stop

	@api.multi
	def do_csvtoexcel(self):
		cad = ""

		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			lst_locations = locat_ids.ids
		else:
			lst_locations = self.location_ids.ids
		lst_products  = self.products_ids.ids
		productos='{'
		almacenes='{'
		date_ini=self.fini
		date_fin=self.ffin
		if self.allproducts:
			lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids
		else:
			lst_products = self.products_ids.ids
		if len(lst_products) == 0:
			raise osv.except_osv('Alerta','No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'

		period_ini = self.period_ini
		period_end = self.period_end

		import io
		from xlsxwriter.workbook import Workbook

		def set_format(workbook):
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(10)
			boldbord.set_bg_color('#DCE6F1')
			boldbord.set_font_name('Times New Roman')

			especial1 = workbook.add_format()
			especial1.set_align('center')
			especial1.set_align('vcenter')
			especial1.set_border(style=1)
			especial1.set_text_wrap()
			especial1.set_font_size(10)
			especial1.set_font_name('Times New Roman')

			especial3 = workbook.add_format({'bold': True})
			especial3.set_align('center')
			especial3.set_align('vcenter')
			especial3.set_border(style=1)
			especial3.set_text_wrap()
			especial3.set_bg_color('#DCE6F1')
			especial3.set_font_size(15)
			especial3.set_font_name('Times New Roman')

			numberdos = workbook.add_format({'num_format':'0.00'})
			numberdos.set_border(style=1)
			numberdos.set_font_size(10)
			numberdos.set_font_name('Times New Roman')

			dateformat = workbook.add_format({'num_format':'d-m-yyyy'})
			dateformat.set_border(style=1)
			dateformat.set_font_size(10)
			dateformat.set_font_name('Times New Roman')

			hourformat = workbook.add_format({'num_format':'hh:mm'})
			hourformat.set_align('center')
			hourformat.set_align('vcenter')
			hourformat.set_border(style=1)
			hourformat.set_font_size(10)
			hourformat.set_font_name('Times New Roman')
			return boldbord,especial1,especial3,numberdos,dateformat,hourformat

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		if self.account_kardex:
			if self.is_resume:
				workbook = Workbook(direccion +'account_vs_kardex_resume.xlsx')
				boldbord,especial1,especial3,numberdos,dateformat,hourformat = set_format(workbook)
				worksheet = workbook.add_worksheet("ACCOUNT vs KARDEX RESUMEN")
				worksheet.set_tab_color('blue')
				sql = """
					select
					gld.codigo||'-'||gld.tipodocumento||'-'||gld.numero as ide,
					max(gld.numero) as numero,
					sum(debe) as debe
					from (
						select *
						from get_libro_diario(periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
						where cuenta like '60%'
					)gld
					group by ide
				"""
				self.env.cr.execute(sql)
				result = self.env.cr.dictfetchall()
				self.env.cr.execute("""
					select T.doc_partner||'-'||T.type_doc||'-'||T.serial||'-'||T.nro as ide,
					sum(T.debit) as debit,
					max(T.stock_doc) as stock_doc,
					max(T.serial) as serial,
					max(T.nro) as nro
					from (
						select
						get_kardex_v.fecha_albaran,
						get_kardex_v.fecha,
						get_kardex_v.type_doc,
						get_kardex_v.serial,
						get_kardex_v.nro,
						get_kardex_v.stock_doc,
						get_kardex_v.doc_partner,
						get_kardex_v.name,
						get_kardex_v.operation_type,
						get_kardex_v.name_template,
						get_kardex_v.unidad,
						get_kardex_v.ingreso,
						round(get_kardex_v.debit,6) as debit,
						get_kardex_v.salida,
						round(get_kardex_v.credit,6) as credit,
						get_kardex_v.saldof,
						round(get_kardex_v.saldov,6) as saldov,
						round(get_kardex_v.cadquiere,6) as cadquiere,
						round(get_kardex_v.cprom,6) as cprom,
						get_kardex_v.origen,
						get_kardex_v.destino,
						get_kardex_v.almacen,
						coalesce(product_product.default_code,product_template.default_code) as code,
						stock_picking.numberg
						from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])
						left join stock_move on get_kardex_v.stock_moveid = stock_move.id
						left join product_product on product_product.id = stock_move.product_id
						left join product_template on product_template.id = product_product.product_tmpl_id
						left join stock_picking on stock_move.picking_id = stock_picking.id
						where get_kardex_v.origen like '%/Proveedores'
						and get_kardex_v.destino like '%/Existencias'
						order by get_kardex_v.correlativovisual
					)T
					group by ide
				""")
				kardex_result = self.env.cr.dictfetchall()
				x = 1
				worksheet.write(x,0,"Numero",boldbord)
				worksheet.write(x,1,"Doc. Almacen",boldbord)
				worksheet.write(x,2,"Valor Contabilidad",boldbord)
				worksheet.write(x,3,"Valor Kardex",boldbord)
				worksheet.write(x,4,"Diferencia",boldbord)
				x=2
				for line in result:
					amount = 0
					kardex_line = filter(lambda k:k['ide'] == line['ide'],kardex_result)
					if kardex_line:
						kardex_line = kardex_line[0]
						amount = line['debe'] - kardex_line['debit']
						serial = kardex_line['serial'] if kardex_line['serial'] else ''
						nro = kardex_line['nro'] if kardex_line['nro'] else ''
						if kardex_line['serial'] and kardex_line['nro']:
							worksheet.write(x,0,kardex_line['serial'] + '-' + kardex_line['nro'],especial1)
						elif kardex_line['nro']:
							worksheet.write(x,0,kardex_line['nro'],especial1)
						elif kardex_line['serial']:
							worksheet.write(x,0,kardex_line['serial'],especial1)
						else:
							worksheet.write(x,0,'',especial1)
						worksheet.write(x,1,kardex_line['stock_doc'] if kardex_line['stock_doc'] else '',especial1)
						worksheet.write(x,2,line['debe'] if line['debe'] else '',numberdos)
						worksheet.write(x,3,kardex_line['debit'] if kardex_line['debit'] else '',numberdos)
						worksheet.write(x,4,amount,numberdos)
					else:
						worksheet.write(x,0,line['numero'] if line['numero'] else '',especial1)
						worksheet.write(x,1,'',especial1)
						worksheet.write(x,2,line['debe'] if line['debe'] else '',numberdos)
						worksheet.write(x,3,0,numberdos)
						worksheet.write(x,4,line['debe'] if line['debe'] else '',numberdos)
					x += 1
				tam_col = [15,15,10,10,10]
				worksheet.set_column('A:A', tam_col[0])
				worksheet.set_column('B:B', tam_col[1])
				worksheet.set_column('C:C', tam_col[2])
				worksheet.set_column('D:D', tam_col[3])
				worksheet.set_column('E:E', tam_col[4])
				f = open(direccion + 'account_vs_kardex_resume.xlsx', 'rb')
				sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
				vals = {
					'output_name': 'Contabilidad vs Kardex Resumen.xlsx',
					'output_file': base64.encodestring(''.join(f.readlines())),
				}
				sfs_id = self.env['custom.export.file'].create(vals)

				return {
				    "type": "ir.actions.act_window",
				    "res_model": "custom.export.file",
				    "views": [[False, "form"]],
				    "res_id": sfs_id.id,
				    "target": "new",
				}

			else:
				workbook = Workbook(direccion +'account_vs_kardex.xlsx')
				boldbord,especial1,especial3,numberdos,dateformat,hourformat = set_format(workbook)
				worksheet = workbook.add_worksheet("ACCOUNT vs KARDEX")
				worksheet.set_tab_color('blue')
				sql = """
					select
					gld.codigo||'-'||gld.tipodocumento||'-'||gld.numero as ide,
					sum(debe) as debe
					from (
						select *
						from get_libro_diario(periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
						where cuenta like '60%'
					)gld
					where (gld.codigo||'-'||gld.tipodocumento||'-'||gld.numero) not in (select coalesce(gkv.doc_partner||'-'||gkv.type_doc||'-'||gkv.serial||'-'||gkv.nro,'False') as IDE
																						from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) gkv
																						where gkv.origen like '%/Proveedores'
																						and gkv.destino like '%/Existencias')
					group by ide
				"""
				self.env.cr.execute(sql)
				result = self.env.cr.dictfetchall()
				if len(result) == 0:
					raise UserError('No se encontro resultados')
				self.env.cr.execute("""
					select
					gld.periodo as periodo,
					gld.libro as libro,
					gld.voucher as voucher,
					gld.cuenta as cuenta,
					gld.debe as debe,
					gld.haber as haber,
					gld.divisa as divisa,
					gld.tipodecambio as tipodecambio,
					gld.importedivisa as importedivisa,
					gld.codigo as codigo,
					gld.tipodocumento as tipodocumento,
					gld.numero as numero,
					gld.fechaemision as fechaemision,
					gld.fechavencimiento as fechavencimiento,
					gld.ctaanalitica as ctaanalitica,
					gld.refconcil as refconcil,
					gld.state as state
					from get_libro_diario(periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) gld
					where (gld.codigo||'-'||gld.tipodocumento||'-'||gld.numero) in (%s)
					and cuenta like '60%%'
				"""%((',').join(["'"+line['ide']+"'" for line in result if line['ide']]))
				)
				result = self.env.cr.dictfetchall()
				x = 1
				worksheet.write(x,0,"Periodo.",boldbord)
				worksheet.write(x,1,"Libro",boldbord)
				worksheet.write(x,2,"Voucher",boldbord)
				worksheet.write(x,3,"Cuenta",boldbord)
				worksheet.write(x,4,"Debe",boldbord)
				worksheet.write(x,5,"Haber",boldbord)
				worksheet.write(x,6,"Divisa",boldbord)
				worksheet.write(x,7,"Tipo Cambio",boldbord)
				worksheet.write(x,8,"Importe Divisa",boldbord)
				worksheet.write(x,9,"Codigo",boldbord)
				worksheet.write(x,10,"Tipo Documento",boldbord)
				worksheet.write(x,11,"Numero",boldbord)
				worksheet.write(x,12,"Fecha Emision",boldbord)
				worksheet.write(x,13,"Fecha Vencimiento",boldbord)
				worksheet.write(x,14,"Cta. Analitica",boldbord)
				worksheet.write(x,15,"Referencia Conciliacion",boldbord)
				worksheet.write(x,16,"Estado",boldbord)
				x=2
				for line in result:
					worksheet.write(x,0,line['periodo'] if line['periodo'] else '',especial1)
					worksheet.write(x,1,line['libro'] if line['libro'] else '',especial1)
					worksheet.write(x,2,line['voucher'] if line['voucher'] else '',especial1)
					worksheet.write(x,3,line['cuenta'] if line['cuenta'] else '',especial1)
					worksheet.write(x,4,line['debe'] if line['debe'] else 0,numberdos)
					worksheet.write(x,5,line['haber'] if line['haber'] else 0,numberdos)
					worksheet.write(x,6,line['divisa'] if line['divisa'] else '',especial1)
					worksheet.write(x,7,line['tipodecambio'] if line['tipodecambio'] else '',especial1)
					worksheet.write(x,8,line['importedivisa'] if line['importedivisa'] else 0,numberdos)
					worksheet.write(x,9,line['codigo'] if line['codigo'] else '',especial1)
					worksheet.write(x,10,line['tipodocumento'] if line['tipodocumento'] else '',especial1)
					worksheet.write(x,11,line['numero'] if line['numero'] else '',especial1)
					worksheet.write(x,12,line['fechaemision'] if line['fechaemision'] else '',especial1)
					worksheet.write(x,13,line['fechavencimiento'] if line['fechavencimiento'] else '',especial1)
					worksheet.write(x,14,line['ctaanalitica'] if line['ctaanalitica'] else '',especial1)
					worksheet.write(x,15,line['refconcil'] if line['refconcil'] else '',especial1)
					worksheet.write(x,16,line['state'] if line['state'] else '',especial1)
					x += 1
				
				tam_col = [9,9,15,9,10,
						   16,14,12,15,10,
						   16,12,14,14,14,
						   8,8,8,8,12,
						   8,20,20,20]

				worksheet.set_column('A:A', tam_col[0])
				worksheet.set_column('B:B', tam_col[1])
				worksheet.set_column('C:C', tam_col[2])
				worksheet.set_column('D:D', tam_col[3])
				worksheet.set_column('E:E', tam_col[4])
				worksheet.set_column('F:F', tam_col[5])
				worksheet.set_column('G:G', tam_col[6])
				worksheet.set_column('H:H', tam_col[7])
				worksheet.set_column('I:I', tam_col[8])
				worksheet.set_column('J:J', tam_col[9])
				worksheet.set_column('K:K', tam_col[10])
				worksheet.set_column('L:L', tam_col[11])
				worksheet.set_column('M:M', tam_col[12])
				worksheet.set_column('N:N', tam_col[13])
				worksheet.set_column('O:O', tam_col[14])
				worksheet.set_column('P:P', tam_col[15])
				worksheet.set_column('Q:Q', tam_col[16])
				worksheet.set_column('R:R', tam_col[17])
				worksheet.set_column('S:S', tam_col[18])
				worksheet.set_column('T:T', tam_col[19])
				worksheet.set_column('U:U', tam_col[20])
				worksheet.set_column('V:V', tam_col[21])
				worksheet.set_column('W:W', tam_col[22])
				worksheet.set_column('X:X', tam_col[23])
				workbook.close()

				f = open(direccion + 'account_vs_kardex.xlsx', 'rb')
				sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
				vals = {
					'output_name': 'Contabilidad vs Kardex.xlsx',
					'output_file': base64.encodestring(''.join(f.readlines())),
				}
				sfs_id = self.env['custom.export.file'].create(vals)

				return {
				    "type": "ir.actions.act_window",
				    "res_model": "custom.export.file",
				    "views": [[False, "form"]],
				    "res_id": sfs_id.id,
				    "target": "new",
				}
		else:
			if self.is_resume:
				workbook = Workbook(direccion +'kardex_vs_account_resume.xlsx')
				boldbord,especial1,especial3,numberdos,dateformat,hourformat = set_format(workbook)
				worksheet = workbook.add_worksheet("KARDEX vs ACCOUNT")
				worksheet.set_tab_color('blue')
				sql = """
					select T.doc_partner||'-'||T.type_doc||'-'||T.serial||'-'||T.nro as ide,
					sum(debit) as debit,
					max(nro) as nro,
					max(serial) as serial,
					max(stock_doc) as stock_doc
					from (
						select
						get_kardex_v.type_doc,
						get_kardex_v.serial,
						get_kardex_v.nro,
						get_kardex_v.stock_doc,
						get_kardex_v.doc_partner,
						round(get_kardex_v.debit,6) as debit
						from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])
						left join stock_move on get_kardex_v.stock_moveid = stock_move.id
						left join product_product on product_product.id = stock_move.product_id
						left join product_template on product_template.id = product_product.product_tmpl_id
						left join stock_picking on stock_move.picking_id = stock_picking.id
						where get_kardex_v.origen like '%/Proveedores'
						and get_kardex_v.destino like '%/Existencias'
						order by get_kardex_v.correlativovisual
					)T
					group by ide
				"""
				self.env.cr.execute(sql)
				result = self.env.cr.dictfetchall()
				sql = """
					select
					gld.codigo||'-'||gld.tipodocumento||'-'||gld.numero as ide,
					sum(debe) as debe
					from (
						select *
						from get_libro_diario(periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""'))
						where cuenta like '60%'
					)gld
					group by ide"""
				self.env.cr.execute(sql)
				account_result = self.env.cr.dictfetchall()
				x = 1
				worksheet.write(x,0,"Serie",boldbord)
				worksheet.write(x,1,"Numero",boldbord)
				worksheet.write(x,2,"Doc. Almacen",boldbord)
				worksheet.write(x,3,"Valor Kardex",boldbord)
				worksheet.write(x,4,"Valor Contabilidad",boldbord)
				worksheet.write(x,5,"Diferencia",boldbord)
				x=2
				for line in result:
					worksheet.write(x,0,line['serial'] if line['serial'] else '',especial1)
					worksheet.write(x,1,line['nro'] if line['nro'] else '',especial1)
					worksheet.write(x,2,line['stock_doc'] if line['stock_doc'] else '',especial1)
					worksheet.write(x,3,line['debit'] if line['debit'] else '',numberdos)
					amount = 0
					account_line = filter(lambda al:al['ide'] == line['ide'],account_result)
					if account_line:
						account_line = account_line[0]
						amount = line['debit'] - account_line['debe']
						worksheet.write(x,4,account_line['debe'] if account_line['debe'] else '',numberdos)
						worksheet.write(x,5,amount,numberdos)
					else:
						worksheet.write(x,4,0,numberdos)
						worksheet.write(x,5,line['debit'] if line['debit'] else '',numberdos)
					x += 1
				tam_col = [10,10,15,10,10,10]
				worksheet.set_column('A:A', tam_col[0])
				worksheet.set_column('B:B', tam_col[1])
				worksheet.set_column('C:C', tam_col[2])
				worksheet.set_column('D:D', tam_col[3])
				worksheet.set_column('E:E', tam_col[4])
				worksheet.set_column('F:F', tam_col[5])
				f = open(direccion + 'kardex_vs_account_resume.xlsx', 'rb')
				sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
				vals = {
					'output_name': 'Kardex vs Contabilidad Resumen.xlsx',
					'output_file': base64.encodestring(''.join(f.readlines())),
				}
				sfs_id = self.env['custom.export.file'].create(vals)

				return {
				    "type": "ir.actions.act_window",
				    "res_model": "custom.export.file",
				    "views": [[False, "form"]],
				    "res_id": sfs_id.id,
				    "target": "new",
				}
			else:
				workbook = Workbook(direccion +'kardex_vs_account.xlsx')
				boldbord,especial1,especial3,numberdos,dateformat,hourformat = set_format(workbook)
				worksheet = workbook.add_worksheet("KARDEX vs ACCOUNT")
				worksheet.set_tab_color('blue')
				self.env.cr.execute("""
					select T.doc_partner||'-'||T.type_doc||'-'||T.serial||'-'||T.nro as ide,
					sum(debit) as debit,
					max(nro) as nro,
					max(serial) as serial,
					max(stock_doc) as stock_doc
					from (
						select
						get_kardex_v.fecha_albaran,
						get_kardex_v.fecha,
						get_kardex_v.type_doc,
						get_kardex_v.serial,
						get_kardex_v.nro,
						get_kardex_v.stock_doc,
						get_kardex_v.doc_partner,
						get_kardex_v.name,
						get_kardex_v.operation_type,
						get_kardex_v.name_template,
						get_kardex_v.unidad,
						get_kardex_v.ingreso,
						round(get_kardex_v.debit,6) as debit,
						get_kardex_v.salida,
						round(get_kardex_v.credit,6) as credit,
						get_kardex_v.saldof,
						round(get_kardex_v.saldov,6) as saldov,
						round(get_kardex_v.cadquiere,6) as cadquiere,
						round(get_kardex_v.cprom,6) as cprom,
						get_kardex_v.origen,
						get_kardex_v.destino,
						get_kardex_v.almacen,
						coalesce(product_product.default_code,product_template.default_code) as code,
						stock_picking.numberg
						from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])
						left join stock_move on get_kardex_v.stock_moveid = stock_move.id
						left join product_product on product_product.id = stock_move.product_id
						left join product_template on product_template.id = product_product.product_tmpl_id
						left join stock_picking on stock_move.picking_id = stock_picking.id
						where get_kardex_v.origen like '%/Proveedores'
						and get_kardex_v.destino like '%/Existencias'
						order by get_kardex_v.correlativovisual
					)T
					where (T.doc_partner||'-'||T.type_doc||'-'||T.serial||'-'||T.nro) not in (select coalesce(gld.codigo||'-'||gld.tipodocumento||'-'||gld.numero,'False') as IDE
																							  from get_libro_diario(periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) gld
																							  where cuenta like '60%')
					group by ide
				""")
				result = self.env.cr.dictfetchall()
				if len(result) == 0:
					raise UserError('No se encontro resultados')
				x = 1
				worksheet.write(x,0,"Fecha Alm.",boldbord)
				worksheet.write(x,1,"Fecha",boldbord)
				worksheet.write(x,2,"Tipo",boldbord)
				worksheet.write(x,3,"Serie",boldbord)
				worksheet.write(x,4,"Numero",boldbord)
				worksheet.write(x,5,"Guia de remision",boldbord)
				worksheet.write(x,6,"Doc. Almacen",boldbord)
				worksheet.write(x,7,"RUC",boldbord)
				worksheet.write(x,8,"Empresa",boldbord)
				worksheet.write(x,9,"T. OP.",boldbord)
				worksheet.write(x,10,"Codigo",boldbord)
				worksheet.write(x,11,"Producto",boldbord)
				worksheet.write(x,12,"Unidad",boldbord)
				worksheet.write(x,13,"Cantidad",boldbord)
				worksheet.write(x,14,"Costo",boldbord)
				worksheet.write(x,15,"Cantidad2",boldbord)
				worksheet.write(x,16,"Costo2",boldbord)
				worksheet.write(x,17,"Cantidad3",boldbord)
				worksheet.write(x,18,"Costo3",boldbord)
				worksheet.write(x,19,"Costo Adquisicion",boldbord)
				worksheet.write(x,20,"Costo Promedio",boldbord)
				worksheet.write(x,21,"Ubicacion Origen",boldbord)
				worksheet.write(x,22,"Ubicacion Destino",boldbord)
				worksheet.write(x,23,"Almacen",boldbord)
				self.env.cr.execute("""
					select
					get_kardex_v.fecha_albaran,
					get_kardex_v.fecha,
					get_kardex_v.type_doc,
					get_kardex_v.serial,
					get_kardex_v.nro,
					get_kardex_v.stock_doc,
					get_kardex_v.doc_partner,
					get_kardex_v.name,
					get_kardex_v.operation_type,
					get_kardex_v.name_template,
					get_kardex_v.unidad,
					get_kardex_v.ingreso,
					round(get_kardex_v.debit,6) as debit,
					get_kardex_v.salida,
					round(get_kardex_v.credit,6) as credit,
					get_kardex_v.saldof,
					round(get_kardex_v.saldov,6) as saldov,
					round(get_kardex_v.cadquiere,6) as cadquiere,
					round(get_kardex_v.cprom,6) as cprom,
					get_kardex_v.origen,
					get_kardex_v.destino,
					get_kardex_v.almacen,
					coalesce(product_product.default_code,product_template.default_code) as code,
					stock_picking.numberg
					from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])
					left join stock_move on get_kardex_v.stock_moveid = stock_move.id
					left join product_product on product_product.id = stock_move.product_id
					left join product_template on product_template.id = product_product.product_tmpl_id
					left join stock_picking on stock_move.picking_id = stock_picking.id
					where get_kardex_v.doc_partner||'-'||get_kardex_v.type_doc||'-'||get_kardex_v.serial||'-'||get_kardex_v.nro in (%s)
					order by get_kardex_v.correlativovisual
				"""%((',').join(["'"+line['ide']+"'" for line in result if line['ide']]))
				)
				result = self.env.cr.dictfetchall()
				x=2
				for line in result:
					worksheet.write(x,0,line['fecha_albaran'] if line['fecha_albaran'] else '',especial1)
					worksheet.write(x,1,line['fecha'] if line['fecha'] else '',especial1)
					worksheet.write(x,2,line['type_doc'] if line['type_doc'] else '',especial1)
					worksheet.write(x,3,line['serial'] if line['serial'] else '',especial1)
					worksheet.write(x,4,line['nro'] if line['nro'] else '',especial1)
					worksheet.write(x,5,line['numberg'] if line['numberg'] else '',especial1)
					worksheet.write(x,6,line['stock_doc'] if line['stock_doc'] else '',especial1)
					worksheet.write(x,7,line['doc_partner'] if line['doc_partner'] else '',especial1)
					worksheet.write(x,8,line['name'] if line['name'] else '',especial1)
					worksheet.write(x,9,line['operation_type'] if line['operation_type'] else '',especial1)
					worksheet.write(x,10,line['code'] if line['code'] else '',especial1)
					worksheet.write(x,11,line['name_template'] if line['name_template'] else '',especial1)
					worksheet.write(x,12,line['unidad'] if line['unidad'] else '',especial1)
					worksheet.write(x,13,line['ingreso'] if line['ingreso'] else 0,numberdos)
					worksheet.write(x,14,line['debit'] if line['debit'] else 0,numberdos)
					worksheet.write(x,15,line['salida'] if line['salida'] else 0,numberdos)
					worksheet.write(x,16,line['credit'] if line['credit'] else 0,numberdos)
					worksheet.write(x,17,line['saldof'] if line['saldof'] else 0,numberdos)
					worksheet.write(x,18,line['saldov'] if line['saldov'] else 0,numberdos)
					worksheet.write(x,19,line['cadquiere'] if line['cadquiere'] else 0,numberdos)
					worksheet.write(x,20,line['cprom'] if line['cprom'] else 0,numberdos)
					worksheet.write(x,21,line['origen'] if line['origen'] else '',especial1)
					worksheet.write(x,22,line['destino'] if line['destino'] else '',especial1)
					worksheet.write(x,23,line['almacen'] if line['almacen'] else '',especial1)
					x += 1

				tam_col = [9,9,5,9,10,
						   16,14,12,60,6,
						   16,40,10,8,8,
						   8,8,8,8,12,
						   8,20,20,20]

				worksheet.set_column('A:A', tam_col[0])
				worksheet.set_column('B:B', tam_col[1])
				worksheet.set_column('C:C', tam_col[2])
				worksheet.set_column('D:D', tam_col[3])
				worksheet.set_column('E:E', tam_col[4])
				worksheet.set_column('F:F', tam_col[5])
				worksheet.set_column('G:G', tam_col[6])
				worksheet.set_column('H:H', tam_col[7])
				worksheet.set_column('I:I', tam_col[8])
				worksheet.set_column('J:J', tam_col[9])
				worksheet.set_column('K:K', tam_col[10])
				worksheet.set_column('L:L', tam_col[11])
				worksheet.set_column('M:M', tam_col[12])
				worksheet.set_column('N:N', tam_col[13])
				worksheet.set_column('O:O', tam_col[14])
				worksheet.set_column('P:P', tam_col[15])
				worksheet.set_column('Q:Q', tam_col[16])
				worksheet.set_column('R:R', tam_col[17])
				worksheet.set_column('S:S', tam_col[18])
				worksheet.set_column('T:T', tam_col[19])
				worksheet.set_column('U:U', tam_col[20])
				worksheet.set_column('V:V', tam_col[21])
				worksheet.set_column('W:W', tam_col[22])
				worksheet.set_column('X:X', tam_col[23])
				workbook.close()

				f = open(direccion + 'kardex_vs_account.xlsx', 'rb')
				sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
				vals = {
					'output_name': 'Kardex vs Contabilidad.xlsx',
					'output_file': base64.encodestring(''.join(f.readlines())),
				}
				sfs_id = self.env['custom.export.file'].create(vals)

				return {
				    "type": "ir.actions.act_window",
				    "res_model": "custom.export.file",
				    "views": [[False, "form"]],
				    "res_id": sfs_id.id,
				    "target": "new",
				}