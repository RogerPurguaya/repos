# -*- encoding: utf-8 -*-
import base64,codecs,pprint,math,string
from cgi import escape
import decimal

from odoo import api, fields, models, _, tools
from datetime import datetime

class reportewizard(models.TransientModel):
	_name = 'reporte.wizard'

	start_date = fields.Date(default=lambda self: fields.Date.context_today(self),string="Fecha Inicio : ") 
	end_date = fields.Date(default=lambda self: fields.Date.context_today(self),string="Fecha Fin : ")
	# stage = fields.Selection([('optimizado','Optimizado'),('lavado','Lavado'),('corte','Corte'),('pulido','Pulido'),('templado','Templado'),('entalle','Entalle'),('ingresado','Ingresado'),('entregado','Entregado')],string='Etapa :',default='optimizado')
	stage_id = fields.Many2one('glass.stage',string='Etapa',domain=[('name','in',('optimizado','lavado','corte','pulido','templado','producido','entalle','ingresado','entregado'))])
	show_all = fields.Boolean('Mostrar todos')

	@api.model_cr
	def init(self):
		self.env.cr.execute(""" 
			drop view if exists report_control_excel;
		create or replace view report_control_excel as (
	select 
	gor.name as op,
	glt.nro_cristal,
	glot.name as lote,
	glt.base1,
	glt.base2,
	glt.altura1,
	glt.altura2,
	scpl.entalle,
	gsr.date,
	rp.nro_documento,
	rp.name as partner,
	gor.obra,
	gor.date_delivery,
	null as observacion,
	CASE WHEN glt.producido is null THEN 'En Proceso' ELSE 'Producido' END as estado,
	1 as cant,
	glt.area,
	ROUND(pt.weight * glt.area,4) as peso,
	rp2.name as user,
	pt.id as id_prod,
	pt.default_code,
	patv.name as presentacion,
	pt.name as producto,
	gs.name,
	glt.corte as corte,
	glt.pulido as pulido,
	glt.lavado as lavado,
	glt.entalle as entalle2,
	glt.templado as templado
		from glass_stage_record gsr
		join glass_stage gs on gs.id = gsr.stage_id
		join glass_lot_line glt on gsr.lot_line_id = glt.id
		join glass_order_line gol on glt.order_line_id = gol.id
		join glass_order gor on gol.order_id = gor.id
		join glass_lot glot on glt.lot_id = glot.id
		join sale_order so on gor.sale_order_id = so.id
		join res_partner rp on so.partner_id = rp.id
		join product_product pp on glt.product_id = pp.id
		join product_template pt on pp.product_tmpl_id = pt.id
		join product_selecionable psel on psel.product_id = pt.id and psel.atributo_id = 4 -- Atributo Espesor
		join product_atributo_valores patv on psel.valor_id = patv.id and psel.atributo_id = patv.atributo_id
		join glass_sale_calculator_line scpl on scpl.id = glt.calc_line_id
		join res_users rus on rus.id = gsr.user_id
		join res_partner rp2 on rp2.id = rus.partner_id
		where gsr.done = true
		order by gsr.stage,op,nro_cristal
			);

			""")

	@api.multi
	def do_rebuild(self):
		results = None
		if self.show_all:
			self.env.cr.execute("""
				select * from report_control_excel WHERE date >= '"""+self.start_date+"""'::date
				AND date < ('"""+self.end_date+"""'::date + '1 day'::interval); 
			""")
			results = self.env.cr.fetchall()
		elif not self.show_all and self.stage_id:
			cast_stage = str(self.stage_id.name)
			self.env.cr.execute("""
				select * from report_control_excel WHERE date >= '"""+self.start_date+"""'::date
				AND date < ('"""+self.end_date+"""'::date + '1 day'::interval) AND stage LIKE '"""+cast_stage+"""'; 
			""")
			results = self.env.cr.fetchall()
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		path = self.env['main.parameter'].search([])[0].dir_create_file
		file_name = 'Reporte de Procesos.xlsx'
		path+=file_name
		workbook = Workbook(path)
		## PRIMERA HOJA
		worksheet = workbook.add_worksheet("DETALLE")
		#Print Format
		worksheet.set_landscape() #Horizontal
		worksheet.set_paper(9) #A-4
		worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		worksheet.fit_to_pages(1, 0)  # Ajustar por Columna 

		bold = workbook.add_format({'bold': False})
		bold.set_align('center')
		bold.set_align('vcenter')

		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(9)
		boldbord.set_bg_color('#DCE6F1')
		bold2 = workbook.add_format({'bold': False})
		bold2.set_align('center')
		bold2.set_align('vcenter')
		bold2.set_bg_color('#E9EFF6')
		bold7 = workbook.add_format({'num_format':'0.0000'})
		bold7.set_bg_color('#E9EFF6')
		bold8 = workbook.add_format({'num_format':'0.0000'})
		bold4 = workbook.add_format({'bold': False})
		bold4.set_align('left')
		bold4.set_align('vcenter')
		bold4.set_bg_color('#E9EFF6')
		bold3 = workbook.add_format({'bold': False})
		bold3.set_align('left')
		bold3.set_align('vcenter')
		bold5 = workbook.add_format({'bold': True})
		bold5.set_border(style=2)
		bold5.set_align('center')
		bold5.set_align('vcenter')
		bold6 = workbook.add_format({'bold': True})
		bold6.set_border(style=2)
		bold6.set_align('right')
		bold6.set_align('vcenter')
		# bottom
		bold9 = workbook.add_format({'bold': True})
		bold9.set_border(style=2)
		bold9.set_align('center')
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		numberdosbord = workbook.add_format({'num_format':'0.00','bold': True})
		numberdosbord.set_border(style=1)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_text_wrap()
		bord.set_align('center')
		bord.set_align('vcenter')
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)  
		title = workbook.add_format({'bold': True})
		title.set_align('center')
		title.set_align('vcenter')
		title.set_text_wrap()
		title.set_font_size(20)
		worksheet.set_row(0, 30)
		saldo_inicial = 0
		saldo_tmp = 0 ## saldo acumulativo
				 
		tam_col = [0,0,0,0]
		tam_letra = 1.2
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')    

		worksheet.merge_range(0,0,0,12, u"REPORTE DE PROCESOS", title)
		
		worksheet.write(2,0, u"Orden de Producción", boldbord)
		worksheet.write(2,1, u"Numero de Cristal", boldbord)
		worksheet.write(2,2, u"Lote", boldbord)
		worksheet.write(2,3, u"Base 1", boldbord)
		worksheet.write(2,4, u"Base 2", boldbord)
		worksheet.write(2,5, u"Altura 1", boldbord)
		worksheet.write(2,6, u"Altura 2", boldbord)
		worksheet.write(2,7, u"Entalle", boldbord)
		worksheet.write(2,8, u"Fecha", boldbord)
		worksheet.write(2,9, u"Nro Documento", boldbord)
		worksheet.write(2,10, u"Cliente", boldbord)
		worksheet.write(2,11, u"Obra", boldbord)
		worksheet.write(2,12, u"Fecha de entrega", boldbord)
		worksheet.write(2,13, u"Observación", boldbord)
		worksheet.write(2,14, u"Estado", boldbord)
		worksheet.write(2,15, u"Ocurrencia", boldbord)
		worksheet.write(2,16, u"Area(M2)", boldbord)
		worksheet.write(2,17, u"Peso", boldbord)
		worksheet.write(2,18, u"Usuario Responsable", boldbord)
		worksheet.write(2,19, u"Costo", boldbord)
		worksheet.write(2,20, u"Código", boldbord)
		worksheet.write(2,21, u"Presentación", boldbord)
		worksheet.write(2,22, u"Producto", boldbord)
		worksheet.write(2,23, u"Etapa", boldbord)
		x=3
		sum_cantidad = 0
		sum_area = 0 
		for line in results:
			style1 = bold
			style2 = bold8
			if x%2 == 0:
				style1 = bold2
				style2 = bold7
			worksheet.write(x,0,line[0],style1) # op
			worksheet.write(x,1,line[1],style1) # nro cristal
			worksheet.write(x,2,line[2],style1) # lote
			worksheet.write(x,3,line[3],style1) # base1
			worksheet.write(x,4,line[4],style1) # base2
			worksheet.write(x,5,line[5],style1) # alt 1
			worksheet.write(x,6,line[6],style1) # alt 2
			worksheet.write(x,7,line[7],style1) # entalle
			worksheet.write(x,8,line[8],style1) # fecha
			worksheet.write(x,9,line[9],style1) # nro doc
			worksheet.write(x,10,line[10],style1) # clinte
			worksheet.write(x,11,line[11],style1) # obra
			worksheet.write(x,12,line[12],style1) # fec entrega
			worksheet.write(x,13,line[13],style2) # observ
			worksheet.write(x,14,line[14],style1) # estado
			worksheet.write(x,15,line[15],style1) # ocurrencia
			worksheet.write(x,16,line[16],style2) # area
			worksheet.write(x,17,line[17],style2) # peso
			worksheet.write(x,18,line[18],style1) # usuario
			
			pt = self.env['product.template'].browse(line[19])
			worksheet.write(x,19,pt.standard_price * line[16] if pt.standard_price else 0,style2) # costo

			worksheet.write(x,20,line[20],style1) # codigo
			worksheet.write(x,21,line[21],style1) # presentacion
			worksheet.write(x,22,line[22],style1) # nom prd
			worksheet.write(x,23,line[23],style1) # stage
			sum_area += float(line[16])
			x+=1

		worksheet.write(x,14,"Total",boldbord) # TOTAL
		worksheet.write(x,15,str(len(results)),bold5) # sum cantidad
		worksheet.write(x,16,str(sum_area),bold6) # sum area

		tam_col = [10,9,10,9,9,9,9,9,10,13,35,17,10,10,12,9,10,10,17,10,15,10,38,10]
		alpha,prev,acum = list(string.ascii_uppercase),'',0
		for i,item in enumerate(tam_col):
			worksheet.set_column(prev+alpha[i%26]+':'+prev+alpha[i%26],item)
			if i==26:
				prev = alpha[acum]
				acum+=1

		## SEGUNDA HOJA

		records = []
		Record = self.env['glass.stage.record']
		c_dom = [('date','<=',self.end_date),('date','>=',self.start_date),('done','=',True)]
		if self.show_all:
			records = Record.search(c_dom)
		elif not self.show_all and self.stage_id:
			records = Record.search(c_dom+[('stage_id','=',self.stage_id.id)])
		
		worksheet = workbook.add_worksheet("RESUMEN")
		#Print Format
		worksheet.set_landscape() #Horizontal
		worksheet.set_paper(9) #A-4
		worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		worksheet.fit_to_pages(1, 0)  # Ajustar por Columna
		worksheet.merge_range(0,0,0,2, u"REPORTE DE PROCESOS", title)
		worksheet.write(4,1, u" Producto", boldbord)
		worksheet.merge_range(2,2,2,11, u"PROCESOS", boldbord)
		
		worksheet.merge_range(3,2,3,3, u"CORTE", boldbord)
		worksheet.merge_range(3,4,3,5, u"PULIDO", boldbord)
		worksheet.merge_range(3,6,3,7, u"ENTALLE", boldbord)
		worksheet.merge_range(3,8,3,9, u"LAVADO", boldbord)
		worksheet.merge_range(3,10,3,11, u"TEMPLADO", boldbord)
		worksheet.merge_range(3,12,3,13, u"PRODUCIDO", boldbord)

		for i in range(2,14,2):
			worksheet.write(4,i, u" Cant.", boldbord)
			worksheet.write(4,i+1, u"M2", boldbord)

		worksheet.write(4,14, u" Cantidad", boldbord)
		worksheet.write(4,15, u" Area", boldbord)
		x=5
		sum_cantidad = sum_area = 0

		products = records.mapped('lot_line_id').mapped('product_id')
		for prod in products:
			style1,style2 = bold,bold8
			if x%2 == 0:
				style1,style2 = bold2,bold7
			grouped = records.filtered(lambda x: x.lot_line_id.product_id == prod)
			
			corte   = grouped.filtered(lambda x: x.stage_id.name == 'corte')
			pulido  = grouped.filtered(lambda x: x.stage_id.name == 'pulido')
			entalle = grouped.filtered(lambda x: x.stage_id.name == 'entalle')
			lavado  = grouped.filtered(lambda x: x.stage_id.name == 'lavado')
			templado= grouped.filtered(lambda x: x.stage_id.name == 'templado')
			producido = grouped.filtered(lambda x: x.stage_id.name == 'producido')
			
			worksheet.write(x,1,prod.name,style1) # producto
			worksheet.write(x,2,len(corte),style1)
			worksheet.write(x,3,sum(corte.mapped('lot_line_id').mapped('area')),style2)
			worksheet.write(x,4,len(pulido),style1)
			worksheet.write(x,5,sum(pulido.mapped('lot_line_id').mapped('area')),style2)
			worksheet.write(x,6,len(entalle),style1)
			worksheet.write(x,7,sum(entalle.mapped('lot_line_id').mapped('area')),style2)
			worksheet.write(x,8,len(lavado),style1)
			worksheet.write(x,9,sum(lavado.mapped('lot_line_id').mapped('area')),style2)
			worksheet.write(x,10,len(templado),style1)
			worksheet.write(x,11,sum(templado.mapped('lot_line_id').mapped('area')),style2)
			worksheet.write(x,12,len(producido),style1)
			worksheet.write(x,13,sum(producido.mapped('lot_line_id').mapped('area')),style2)
			
			total = len(grouped)
			total_area = 0
			for i in grouped:
				total_area += i.lot_line_id.area
			worksheet.write(x,14,total,style2)
			worksheet.write(x,15,total_area,style2)
			sum_cantidad += total
			sum_area += total_area
			x+=1

		worksheet.write(x,1,"Total",boldbord) # TOTAL
		worksheet.write(x,14,str(sum_cantidad),bold9) # sum cantidad
		worksheet.write(x,15,str(sum_area),bold6) # sum area

		tam_col = [6,78]+12*[9]+[13,13]
		for i,item in enumerate(tam_col):
			worksheet.set_column(alpha[i]+':'+alpha[i],item)
		workbook.close()

		file = open(path,'rb')
		export = self.env['export.file.manager'].create({
			'file_name': file_name,
			'file': base64.b64encode(file.read()),	
		})
		file.close()
		return export.export_file(clear=True,path=path)