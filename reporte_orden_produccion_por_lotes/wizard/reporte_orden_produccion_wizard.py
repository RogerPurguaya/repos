# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
import codecs, pprint, pytz,base64,decimal
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import simpleSplit,ImageReader
import StringIO

class ReporteOrdenProduccionAlmacen(models.TransientModel):
	_name='reporte.orden.produccion.wizard'
	order_id = fields.Many2one('glass.order')

	@api.multi
	def print_report_op(self):
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
		pdfmetrics.registerFont(TTFont('Calibri-Bold', 'CalibriBold.ttf'))
		path = self.env['main.parameter'].search([])[0].dir_create_file+''
		file_name = 'Reporte OP-'+self.order_id.name+'.pdf'
		path+=file_name
		c = canvas.Canvas(path, pagesize= A4)
		width ,height  = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40
		pos_inicial = hReal-140
		start_pos_left = 20
		size_widths = [25,160,75,30,40,40,40,40,90]
		total_width_size = sum(size_widths)
		totals = [0,0,0,0]
		aux_array = [0,0,0,0,0] # para almacenar auxiliares
		qty_cristales = 0
		pagina = 1
		textPos = 0
		
		self.header(c,wReal,hReal,start_pos_left,size_widths)
		glass_order_lines = self.order_id.line_ids
		
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina,start_pos_left,size_widths)

		for line in glass_order_lines:
			c.setFont("Calibri", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina,start_pos_left,size_widths)

			tmp_pos = start_pos_left
			c.drawRightString(tmp_pos+size_widths[0]-10,pos_inicial,line.crystal_number or '')
			tmp_pos += size_widths[0]

			c.drawString(tmp_pos+2,pos_inicial,line.product_id.name[:160] if line.product_id.name else '')
			tmp_pos += size_widths[1]

			c.drawString(tmp_pos+2, pos_inicial, line.measures)
			tmp_pos += size_widths[2]

			c.drawString(tmp_pos+2, pos_inicial,line.lot_line_id.lot_id.name or '')
			tmp_pos += size_widths[3]
			
			c.drawString(tmp_pos+2, pos_inicial, 'EM' if line.embalado else '')
			tmp_pos += size_widths[4]
			
			state= dict(self.order_id._fields['state'].selection).get(line.order_id.state)
			c.drawString(tmp_pos+2,pos_inicial,state)
			aux_array[0] = tmp_pos+2
			tmp_pos += size_widths[5]

			area = line.area or 0
			c.drawRightString(tmp_pos+size_widths[6]-2,pos_inicial,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % area)))
			aux_array[1] = tmp_pos+size_widths[6]-2
			totals[0] += area
			tmp_pos += size_widths[6]

			peso = line.peso or 0
			c.drawRightString(tmp_pos+size_widths[7]-2,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % peso)))
			totals[1] += peso
			aux_array[2] = tmp_pos+size_widths[7]-2
			tmp_pos += size_widths[7]
			location = line.order_id.warehouse_id.name if (line.order_id.warehouse_id and line.lot_line_id.ingresado) else ''
			c.drawString(tmp_pos+10,pos_inicial,location)
			
		c.line(start_pos_left,pos_inicial-2,start_pos_left+total_width_size,pos_inicial-2)
		c.drawString(start_pos_left, pos_inicial-12,'Nro Pzs.'+str(len(glass_order_lines)))
		c.drawRightString(aux_array[0], pos_inicial-12,'Totales:')
		c.drawRightString(aux_array[1], pos_inicial-12, '{:,.4f}'.format(decimal.Decimal ("%0.4f" % totals[0])))
		c.drawRightString(aux_array[2], pos_inicial-12, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % totals[1])))

		now = fields.Datetime.context_timestamp(self,datetime.now())
		c.drawString(start_pos_left+10, pos_inicial-48,'Usuario: %s %s'%(self.env.user.name,str(now)[:19]))
		c.save()

		with open(path,'rb') as file:
			export = self.env['export.file.manager'].create({
				'file_name': file_name,
				'file': base64.b64encode(file.read()),	
			})
		return export.export_file(clear=True,path=path)

	# header para el segundo reporte
	@api.multi
	def header(self,c,wReal,hReal,start_pos_left,size_widths=None):
		
		company = self.env['res.company'].search([])[0]
		if len(company) == 0:
			raise exceptions.Warning(u"No ha confugurado su Compañía.\n Configure los datos de su compañía para poder mostrarlos en este reporte.")
		
		if company.logo:
			file = base64.b64decode(company.logo)
			c.drawImage(ImageReader(StringIO.StringIO(file)),start_pos_left,792,width=75,height=40,mask=None)
		else:
			c.setFont("Calibri", 12)
			c.drawString(start_pos_left,800,company.name if company.name else 'Company')

		## Codigo temporal:
		invoice = ''
		if self.order_id.invoice_ids:
			invoice = self.order_id.invoice_ids[0].number or ''

		# Datos de Conpañía para la cabecera
		c.setFont("Calibri", 6)
		c.drawString(start_pos_left,784,company.street if company.street else u'Address')
		c.drawString(start_pos_left,778,(u'Teféfono: '+str(company.phone)) if company.phone else 'no disponible')
		c.drawString(start_pos_left+70,778,(u'Fax: '+str(company.fax))if company.fax else 'no disponible')
		c.drawString(start_pos_left,770,company.website if company.website else 'website')
		c.drawString(start_pos_left+100,770,company.email if company.email else 'email')
		ruc = company.partner_id.nro_documento if company.partner_id.nro_documento else ''
		c.drawString(start_pos_left,762,'RUC: '+str(ruc))		
		
		pos_inicial = hReal-83
		posicion_indice = 1
		c.line(375,800,580,800)
		c.line(375,750,580,750)
		c.line(375,800,375,750)
		c.line(580,800,580,750)
		c.setFont("Calibri", 13)
		c.drawString( 410 , 785,u'ORDEN DE PRODUCCIÓN')
		c.drawString( 470 , 765, self.order_id.name)
		for i in range(0,2):
			c.line(start_pos_left,750-i,365,750-i)
		c.line(start_pos_left,745,365,745)
		c.setFont("Calibri", 8) 
		c.drawString(start_pos_left,730,'Documento:')
		c.drawString(start_pos_left+70,730,str(invoice))
		c.drawString(start_pos_left,722,'Cliente:')
		c.drawString(start_pos_left+70,722,self.order_id.partner_id.name)
		c.drawString(start_pos_left,714,'Obra:')
		c.drawString(start_pos_left+70,714, self.order_id.obra if self.order_id.obra else '')
		c.drawString(start_pos_left,706,'Direccion:')
		street   = self.order_id.partner_id.street or ''
		province = self.order_id.partner_id.province_id.name or ''
		district = self.order_id.partner_id.district_id.name or ''
		street  += '/'+province+'/'+district
		c.drawString(start_pos_left+70,706,street)
		c.drawString(start_pos_left,698,'Pto.Llegada:')
		llegada   = self.order_id.sale_order_id.partner_shipping_id.street or ''
		province  = self.order_id.sale_order_id.partner_shipping_id.province_id.name or ''
		district  = self.order_id.sale_order_id.partner_shipping_id.district_id.name or ''
		llegada  += '/'+province+'/'+district
		c.drawString(start_pos_left+70,698,llegada)	
		c.drawString( 380 ,730,u'Fecha Emisión:')
		c.drawString( 460 ,730,str(datetime.strptime(self.order_id.date_order,"%Y-%m-%d %H:%M:%S")-timedelta(hours=5)))
		c.drawString( 380 ,722,u'Fecha Producción:')
		c.drawString( 460 ,722,self.order_id.date_production)
		c.drawString( 380 ,714,'Fecha Despacho:')
		c.drawString( 460 ,714,self.order_id.date_send)
		c.drawString( 380 ,706,'Fecha Entrega:')
		c.drawString( 460 ,706,self.order_id.date_delivery)
		c.drawString( 380 ,698,'Vendedor:')
		c.drawString( 460 ,698,self.order_id.seller_id.partner_id.name)
		c.line(start_pos_left,690,580,690)
		
		total_width = sum(size_widths) + start_pos_left
		c.line(start_pos_left,680,total_width,680)
		c.line(start_pos_left,660,total_width,660)
		c.line(start_pos_left,680,start_pos_left,660)
		c.line(total_width,680,total_width,660)
		headers = ['Cristal','Detalle','Medida','Lote','Embalado','Estado OP','M2','Peso',u'Ubicación']
		if len(headers) != len(size_widths):
			print('El numero de headers y de anchos deben ser iguales :)')
			return
		pos = start_pos_left
		for i,item in enumerate(headers):
			c.drawCentredString(pos +int(size_widths[i]/2),667,item)
			pos += size_widths[i]

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,start_pos_left,size_widths):
		if posactual <40:
			c.showPage()
			self.header(c,wReal,hReal,start_pos_left,size_widths)

			c.setFont("Calibri-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-160
		else:
			return pagina,posactual-valor
