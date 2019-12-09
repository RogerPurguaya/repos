# -*- encoding: utf-8 -*-

import base64,codecs,pprint,string
from openerp import models, fields, api
from datetime import datetime,timedelta
from time import time

class reporte_seguimiento_produccion_wizard(models.TransientModel):
	_name='report.production.tracing.wizard'

	def _get_start_date(self):
		now = datetime.now().date()
		start_date = now - timedelta(days=30,hours=5)
		return start_date

	start_date = fields.Date(string='Fecha Inicio',default=_get_start_date)
	end_date = fields.Date(string='Fecha Fin',default=fields.Date.today)
	search_param = fields.Selection([('glass_order','Orden de Produccion'),('product','Producto')],default='glass_order',string='Busqueda por')
	glass_order_id = fields.Many2one('glass.order','Nro de Orden de Produccion')
	product_id = fields.Many2one('product.product','Nombre de producto')
	filters = fields.Selection([('all','Todos'),('pending','En proceso'),('produced','Producidos'),('to inter','Por ingresar'),('to deliver','Por Entregar'),('expired','Vencidos')],default='all',string='Estado')
	customer_id = fields.Many2one('res.partner','Cliente')
	show_breaks = fields.Boolean('Mostrar Rotos')
	show_for_dates = fields.Boolean('Mostrar en rango de fechas')

	@api.multi
	def do_rebuild(self):
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		path = self.env['main.parameter'].search([])[0].dir_create_file
		file_name = u'Reporte Seguimiento Producción.xlsx'
		path+=file_name
		workbook = Workbook(path)
		worksheet = workbook.add_worksheet("Seguimiento de Produccion")
		#Print Format
		worksheet.set_landscape() #Horizontal
		worksheet.set_paper(9) #A-4
		worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		worksheet.fit_to_pages(1, 0)  # Ajustar por Columna	
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(9)
		boldbord.set_bg_color('#DCE6F1')
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_text_wrap()
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)	
		title = workbook.add_format({'bold': True})
		title.set_align('center')
		title.set_align('vcenter')
		title.set_text_wrap()
		title.set_font_size(20)
		worksheet.set_row(0, 30)
		boldborda = workbook.add_format({'bold': True})
		boldborda.set_border(style=2)
		boldborda.set_align('center')
		boldborda.set_align('vcenter')
		boldborda.set_text_wrap()
		boldborda.set_font_size(9)
		boldborda.set_bg_color('#ffff40')

		x= 9 # caminador de iteraciones para cada linea			
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.2
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		# display values for selection fields:
		param = search = ''
		if not self.show_for_dates and self.search_param:
			search= dict(self._fields['search_param'].selection).get(self.search_param)
			label = "PRODUCTO:" if search=='Producto' else 'OP:'
			param = self.glass_order_id.name if self.glass_order_id.name else self.product_id.name
		else:
			label = 'Rango de fechas'
		state = dict(self._fields['filters'].selection).get(self.filters)
		worksheet.merge_range(1,1,0,7, u"REPORTE DE SEGUIMIENTO GLOBAL DE LA PRODUCCION",title)
		worksheet.write(2,1, u"FECHA DEL:",bold)
		worksheet.write(3,1, u"BUSQUEDA:",bold)
		worksheet.write(4,1, label,bold)
		worksheet.write(5,1, u"ESTADO:",bold)
		worksheet.write(2,2, str(self.start_date),bold)
		worksheet.write(2,3, u"AL",bold)
		worksheet.write(2,4, str(self.end_date),bold)
		worksheet.write(3,2, search,bold)
		worksheet.merge_range(4,2,4,3,param,bold)
		worksheet.write(5,2, state,bold)

		worksheet.merge_range(7,0,8,0, u"ORDEN DE PRODUCCION",boldbord)
		worksheet.merge_range(7,1,8,1, u"LOTES",boldbord)
		worksheet.merge_range(7,2,8,2, u"FECHA DE PRODUCCION",boldbord)
		worksheet.merge_range(7,3,8,3, u"FECHA DE ENTREGA",boldbord)
		worksheet.merge_range(7,4,8,4, u"FECHA DE DESPACHO",boldbord) # 
		worksheet.merge_range(7,5,8,5, u"NOMBRE CLIENTE",boldbord)
		worksheet.merge_range(7,6,8,6, u"OBRA",boldbord)
		worksheet.merge_range(7,7,8,7, u"COD PRESENTACION",boldbord)
		worksheet.merge_range(7,8,8,8, u"DESCRIPCION DE PRODUCTO",boldbord)
		worksheet.merge_range(7,9,8,9, u"DOCUMENTO",boldbord)
		worksheet.merge_range(7,10,8,10, u"TIPO DOC.",boldbord)
		worksheet.merge_range(7,11,8,11, u"RUC PARTNER",boldbord)
		worksheet.merge_range(7,12,8,12, u"VENDEDOR",boldbord)
		worksheet.merge_range(7,13,8,13, u"PTO. LLEGADA",boldbord)
		worksheet.merge_range(7,14,8,14, u"PROVINCIA",boldbord)
		worksheet.merge_range(7,15,8,15, u"NRO PENDIENTES",boldbord)
		worksheet.merge_range(7,16,8,16, u"AREA PENDIENTE(M2)",boldbord)
		worksheet.merge_range(7,17,8,17, u"ESTADO OP",boldbord)
		worksheet.merge_range(7,18,8,18, u"FECHA DESPACHO REAL",boldbord)
		worksheet.merge_range(7,19,8,19, u"DIAS DESPACHO",boldbord)
		worksheet.merge_range(7,20,8,20, u"AÑO",boldbord)
		worksheet.merge_range(7,21,8,21, u"MES",boldbord)
		worksheet.merge_range(7,22,8,22, u"SEMANA",boldbord)
		worksheet.merge_range(7,23,8,23, u"TOTAL M2 SOLICITADOS",boldbord)
		worksheet.merge_range(7,24,8,24, u"TOTAL VIDRIOS SOLICITADOS",boldbord)		
		worksheet.merge_range(7,25,8,25, u"TOTAL M2 SOLICITADOS CON ENTALLE",boldbord)
		worksheet.merge_range(7,26,8,26, u"TOTAL VIDRIOS CON ENTALLE",boldbord)

		worksheet.merge_range(7,27,7,28, u"OPTIMIZADO",boldbord)
		worksheet.merge_range(7,29,7,30, u"CORTE",boldbord)
		worksheet.merge_range(7,31,7,32, u"PULIDO",boldbord)
		worksheet.merge_range(7,33,7,34, u"ENTALLE",boldbord)
		worksheet.merge_range(7,35,7,36, u"LAVADO",boldbord)
		worksheet.merge_range(7,37,7,38, u"TEMPLADO",boldbord)
		worksheet.merge_range(7,39,7,40, u"INSULADO",boldbord)
		worksheet.merge_range(7,41,7,42, u"LAMINADO",boldbord)
		worksheet.merge_range(7,43,7,44, u"INGRESADO",boldbord)
		worksheet.merge_range(7,45,7,46, u"ENTREGADO",boldbord)
		worksheet.merge_range(7,47,7,48, u"TRANSFERIDOS",boldbord)
		worksheet.merge_range(7,49,7,50, u"ARENADO",boldbord)
		worksheet.merge_range(7,51,7,52, u"COMPRADO",boldbord)
		worksheet.merge_range(7,53,8,53, u"ESTADO",boldbord)

		for i in range(27,53,2):
			worksheet.write(8,i, u"M2 cristales",boldbord)
			worksheet.write(8,i+1, u"Numero de cristales",boldbord)
		
		#valores_dia= [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,]
		#total_values= [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		data = []
		#test = []
		if self.product_id and self.search_param == 'product':
			domain = [('state','in',('process','confirmed','draft'))]
			if self.start_date and self.end_date:
				domain.append(('date_production','>=',self.start_date))
				domain.append(('date_production','<=',self.end_date))
			orders = self.env['glass.order'].search(domain)
			if self.customer_id:
				orders=orders.filtered(lambda x: x.partner_id.id == self.customer_id.id)
			# for item in range(0,1500):
			# 	test.append(orders[0])

			# print('start...', len(test))
			# start_time = time()
			data = self.get_data(orders,self.product_id)
			
		elif self.glass_order_id and self.search_param == 'glass_order':
			if self.start_date and self.end_date:
				start = self._str2date(self.start_date)
				end = self._str2date(self.end_date)
				date_order = self._str2date(self.glass_order_id.date_production)
				if start<=date_order<=end:
					data = self.get_data(self.glass_order_id)
			else:
				data = self.get_data(self.glass_order_id)
		elif self.show_for_dates and self.start_date and self.end_date:
			domain = [('date_production','>=',self.start_date),('date_production','<=',self.end_date)]
			orders = self.env['glass.order'].search(domain)
			data = self.get_data(orders)
			
		for line in data:
			#cont = 0
			worksheet.write(x,0,line['op'],bord)
			worksheet.write(x,1,line['lot_names'],bord)
			worksheet.write(x,2,line['fec_produccion'],bord )
			worksheet.write(x,3,line['fec_entrega'],bord)
			worksheet.write(x,4,line['fec_despacho'],bord)
			worksheet.write(x,5,line['cliente'],bord)
			worksheet.write(x,6,line['obra'],bord)
			worksheet.write(x,7,line['presentacion'],bord)
			worksheet.write(x,8,line['producto'],bord)
			worksheet.write(x,9,line['documento'],bord)
			worksheet.write(x,10,line['tipo_doc'],bord)
			worksheet.write(x,11,line['ruc_partner'],bord)
			worksheet.write(x,12,line['vendedor'],bord)
			worksheet.write(x,13,line['pto_llegada'],bord)
			worksheet.write(x,14,line['provincia'],bord)
			worksheet.write(x,15,line['nro_pendientes'],bord)
			worksheet.write(x,16,line['area_pendientes'],bord)
			worksheet.write(x,17,line['estado_op'],bord)
			worksheet.write(x,18,line['fec_kardex'],bord)
			worksheet.write(x,19,line['dias_kardex'],bord)
			worksheet.write(x,20,line['anio'],bord)
			worksheet.write(x,21,line['mes'],bord)
			worksheet.write(x,22,line['semana'],bord)
			worksheet.write(x,23,line['total_area'],bord)
			worksheet.write(x,24,line['total_vidrios'],bord )
			worksheet.write(x,25,line['area_entalle'],bord )
			worksheet.write(x,26,line['vidrios_entalle'],bord)
			worksheet.write(x,27,line['area_optimizado'],bord)
			worksheet.write(x,28,line['vidrios_optimizado'],bord)
			worksheet.write(x,29,line['area_corte'],bord)
			worksheet.write(x,30,line['vidrios_corte'],bord)
			worksheet.write(x,31,line['area_pulido'],bord)
			worksheet.write(x,32,line['vidrios_pulido'],bord)
			worksheet.write(x,33,line['area_entalle_real'],bord)
			worksheet.write(x,34,line['vidrios_entalle_real'],bord)
			worksheet.write(x,35,line['area_lavado'],bord)
			worksheet.write(x,36,line['vidrios_lavado'],bord)
			worksheet.write(x,37,line['area_templado'],bord)
			worksheet.write(x,38,line['vidrios_templado'],bord)
			worksheet.write(x,39,line['area_insulado'],bord)
			worksheet.write(x,40,line['vidrios_insulado'],bord)
			worksheet.write(x,41,"NA",bord)
			worksheet.write(x,42,"NA",bord)
			worksheet.write(x,43,line['area_ingresado'],bord)
			worksheet.write(x,44,line['vidrios_ingresado'],bord)
			worksheet.write(x,45,line['area_entregado'],bord)
			worksheet.write(x,46,line['vidrios_entregado'],bord)
			worksheet.write(x,47,"-",bord)
			worksheet.write(x,48,"-",bord)
			worksheet.write(x,49,line['area_arenado'],bord)
			worksheet.write(x,50,line['vidrios_arenado'],bord)
			worksheet.write(x,51,line['area_comprado'],bord)
			worksheet.write(x,52,line['vidrios_comprado'],bord)
			worksheet.write(x,53,line['estado'],bord)
			x=x+1
		tam_col = [10,10,10,10,10,24,20,12,30,10,5,13,24,20,10,8,8,12,10,8,5,5,5]+[12 for i in range(33)]
		alpha,prev,acum = list(string.ascii_uppercase),'',0
		for i,item in enumerate(tam_col):
			worksheet.set_column(prev+alpha[i%26]+':'+prev+alpha[i%26],item)
			if i==26:
				prev = alpha[acum]
				acum+=1
		workbook.close()
		#elapsset = time() - start_time
		
		#print('finish: ',elapsset)
		# new 
		file = open(path,'rb').read()
		export = self.env['export.file.manager'].create({
			'file_name': file_name,
			'file': base64.b64encode(file),	
		})
		return export.export_file(clear=True,path=path)

	@api.multi
	def get_data(self,orders,product=None):
		results = []
		for order in orders:
			prods = order.line_ids.filtered(lambda x: x.product_id == product).mapped('product_id') if product else order.line_ids.mapped('product_id')
			filters = self.filters
			for prod in prods:
				lines = order.line_ids.filtered(lambda x: x.product_id.id == prod.id)
				if filters == 'pending':
					lines = lines.filtered(lambda x: not x.lot_line_id.templado)
				elif filters == 'produced':
					lines = lines.filtered(lambda x: x.lot_line_id.templado)
				elif filters == 'to inter':
					lines = lines.filtered(lambda x: x.lot_line_id.templado and  x.lot_line_id.ingresado)
				elif filters == 'to deliver':
					lines = lines.filtered(lambda x: x.lot_line_id.ingresado and not x.lot_line_id.entregado)
				elif filters == 'expired':
					now = (datetime.now()-timedelta(hours=5)).date()
					lines = lines.filtered(lambda x: x.date_production < now and not x.lot_line_id.templado)
				if not self.show_breaks:
					lines = lines.filtered(lambda x: not x.lot_line_id.is_break)			
				if len(lines) == 0 and filters not in ('pending','all'):
					continue
				
				attr = prod.product_tmpl_id.atributo_ids.filtered(lambda x: x.atributo_id.id==4)
				if any(attr):
					attr = attr[0].valor_id.name
				else:
					attr = 'not found'
				## totales desde calculadora
				## empezamos a sacar totales entalle
				sale_lines = order.sale_lines.filtered(lambda x: x.product_id.id == prod.id)
				calc_lines = sale_lines.mapped('id_type_line').filtered(lambda x: x.production_id == order)
				filtered = calc_lines.filtered(lambda x: x.entalle>0)
				area_entalle,vidrios_entalle = '-','-'
				if any(filtered):
					area_entalle=sum(filtered.mapped('area'))
					vidrios_entalle=sum(map(lambda y:y.cantidad,filtered))

				## empezamos a sacar totales arenado
				filtered = calc_lines.filtered(lambda x: x.arenado)
				area_arenado,vidrios_arenado = '-','-'
				if any(filtered):
					area_arenado=sum(filtered.mapped('area'))
					vidrios_arenado=sum(map(lambda y:y.cantidad,filtered))
				
				total_vidrios = sum(calc_lines.mapped('cantidad'))
				vals = {
					'cliente':order.partner_id.name,
					'presentacion': attr,
					'producto': prod.name,
					'total_area': sum(calc_lines.mapped('area')),
					'total_vidrios':total_vidrios,
					'area_entalle':area_entalle,
					'vidrios_entalle':vidrios_entalle,
					'area_arenado':area_arenado,
					'vidrios_arenado':vidrios_arenado,
				}
				lot_lines = lines.mapped('lot_line_id')
				## empezamos a sacar totales optimizado
				filtered = lot_lines.filtered(lambda x: x.optimizado)
				area_optimizado = vidrios_optimizado = '-'
				if any(filtered):
					area_optimizado=sum(filtered.mapped('area'))
					vidrios_optimizado=len(filtered)
				## empezamos a sacar totales corte
				filtered = lot_lines.filtered(lambda x: x.corte)
				area_corte,vidrios_corte = '-','-'
				if any(filtered):
					area_corte=sum(filtered.mapped('area'))
					vidrios_corte=len(filtered)
				## empezamos a sacar totales entalle real
				filtered = lot_lines.filtered(lambda x: x.entalle)
				area_entalle_real,vidrios_entalle_real = '-','-'
				if any(filtered):
					area_entalle_real=sum(filtered.mapped('area'))
					vidrios_entalle_real=len(filtered)
				## empezamos a sacar totales lavado
				filtered = lot_lines.filtered(lambda x: x.lavado)
				area_lavado,vidrios_lavado = '-','-'
				if any(filtered):
					area_lavado=sum(filtered.mapped('area'))
					vidrios_lavado=len(filtered)
				## empezamos a sacar totales templado
				filtered = lot_lines.filtered(lambda x: x.templado)
				area_templado,vidrios_templado = '-','-'
				if any(filtered):
					area_templado=sum(filtered.mapped('area'))
					vidrios_templado=len(filtered)
				## empezamos a sacar totales ingresado
				filtered = lot_lines.filtered(lambda x: x.ingresado)
				area_ingresado,vidrios_ingresado = '-','-'
				if any(filtered):
					area_ingresado=sum(filtered.mapped('area'))
					vidrios_ingresado=len(filtered)
				## empezamos a sacar totales pulido
				filtered = lot_lines.filtered(lambda x: x.pulido)
				area_pulido,vidrios_pulido = '-','-'
				if any(filtered):
					area_pulido=sum(filtered.mapped('area'))
					vidrios_pulido=len(filtered)
				## empezamos a sacar totales insulado
				filtered = lot_lines.filtered(lambda x: x.insulado)
				area_insulado,vidrios_insulado = 'NA','NA'
				if any(filtered):
					area_insulado=sum(filtered.mapped('area'))
					vidrios_insulado=len(filtered)
				## empezamos a sacar totales entregado
				filtered = lot_lines.filtered(lambda x: x.entregado)
				area_entregado,vidrios_entregado = '-','-'
				if any(filtered):
					area_entregado=sum(filtered.mapped('area'))
					vidrios_entregado=len(filtered)
				## empezamos a sacar totales comprado
				filtered = lot_lines.filtered(lambda x: x.comprado)
				area_comprado,vidrios_comprado = '-','-'
				if any(filtered):
					area_comprado=sum(filtered.mapped('area'))
					vidrios_comprado=len(filtered)
				aux = ''
				for i in lot_lines.mapped('lot_id').mapped('name'):
					aux += 'L-'+str(i)+' '

				vals['op'] = order.name
				vals['lot_names'] = aux
				vals['fec_produccion'] = order.date_production.replace('-','/')
				vals['fec_entrega'] = order.date_delivery.replace('-','/')
				vals['fec_despacho'] = order.date_send.replace('-','/')
				vals['obra'] = order.obra if order.obra else ''
				
				invoice = self.env['account.invoice']
				if any(order.invoice_ids):
					invoice = order.invoice_ids[0]
				
				vals['documento'] = invoice.number or ''
				vals['tipo_doc'] = invoice.it_type_document.code or ''
				vals['ruc_partner'] = order.partner_id.nro_documento or ''
				vals['vendedor'] = order.sale_order_id.user_id.name
				vals['pto_llegada'] = order.delivery_street or ''
				vals['provincia'] = order.delivery_province or ''
				try:
					pending = total_vidrios - vidrios_templado
					a_pending = sum(sale_lines.mapped('product_uom_qty')) - area_templado
				except TypeError as e:
					pending = total_vidrios
					a_pending = sum(sale_lines.mapped('product_uom_qty'))
				vals['nro_pendientes']  = pending
				vals['area_pendientes'] = a_pending
				state = dict(order._fields['state'].selection).get(order.state)
				vals['estado_op'] = state

				date_kardex = dias_kardex = ''
				picking = order.sale_order_id.mapped('picking_ids')
				if any(picking):
					if picking[0].state == 'done':
						date_kardex = picking[0].fecha_kardex
						dias_kardex = (self._str2date(date_kardex) - self._str2date(order.date_send)).days

				vals['fec_kardex'] = date_kardex.replace('-','/')
				vals['dias_kardex'] = dias_kardex
				vals['anio'] = datetime.now().date().year
				vals['mes'] = datetime.now().date().month
				vals['semana'] = datetime.now().date().isocalendar()[1]
				
				vals['area_optimizado'] = area_optimizado
				vals['vidrios_optimizado'] = vidrios_optimizado
				vals['area_corte'] = area_corte
				vals['vidrios_corte'] = vidrios_corte
				vals['area_entalle_real'] = area_entalle_real
				vals['vidrios_entalle_real'] = vidrios_entalle_real
				vals['area_lavado'] = area_lavado
				vals['area_pulido']=area_pulido
				vals['area_insulado']=area_insulado
				vals['vidrios_insulado']=vidrios_insulado
				vals['vidrios_pulido']=vidrios_pulido
				vals['vidrios_lavado'] = vidrios_lavado
				vals['area_templado'] = area_templado
				vals['vidrios_templado'] = vidrios_templado
				vals['area_ingresado'] = area_ingresado
				vals['vidrios_ingresado'] = vidrios_ingresado
				vals['area_entregado'] = area_entregado
				vals['vidrios_entregado'] = vidrios_entregado
				vals['area_comprado'] = area_comprado
				vals['vidrios_comprado'] = vidrios_comprado
				state = ''
				if total_vidrios == vidrios_entregado:
					state = 'ENTREGADO'
				if vidrios_ingresado == '-':
					state = 'PENDIENTE'
				if total_vidrios > vidrios_entregado and vidrios_entregado>0:
					state = 'PARCIALMENTE ENTREGADO'
				vals['estado'] = state
				results.append(vals)

		return results

	def _str2date(self,string):
			return datetime.strptime(string,"%Y-%m-%d").date()
