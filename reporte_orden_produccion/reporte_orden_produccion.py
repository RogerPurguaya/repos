# -*- coding: utf-8 -*-
import base64,decimal
from openerp import models, fields, api, exceptions
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import  cm
from reportlab.lib.utils import ImageReader
import StringIO

class GlassOrder(models.Model):
	_inherit='glass.order'

	@api.multi
	def ordenprod_buttom(self):
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
		pdfmetrics.registerFont(TTFont('Calibri-Bold', 'CalibriBold.ttf'))
		width ,height  =A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40
		check = 'X'
		path = self.env['main.parameter'].search([])[0].dir_create_file
		file_name = u'Orden de Producción '+self.name+'.pdf'
		path+=file_name
		c = canvas.Canvas(path, pagesize= A4)
		pos_inicial = hReal-165
		start_pos_left = 20
		size_widths = [70,104,78,16,16,16,16,16,70,70]
		totals = [0,0,0,0]
		aux_array = [0,0,0,0,0] # para almacenar auxiliares
		qty_cristales = 0
		pagina = 1
		textPos = 0
		self.cabezera_op(c,wReal,hReal,start_pos_left)
		glass_order_lines = self.sale_lines
		pagina, pos_inicial = self.verify_linea_op(c,wReal,hReal,pos_inicial,12,pagina,start_pos_left)

		for item in glass_order_lines:
			#weight = self.env['product.product'].search([('id','=',item.product_id[0].id)])
			c.setFont("Calibri-Bold", 8)
			pagina, pos_inicial = self.verify_linea_op(c,wReal,hReal,pos_inicial,40,pagina,start_pos_left)
			weight_pro = item.product_id.weight if item.product_id.weight else 0
			c.drawString(start_pos_left, pos_inicial, item.name if item.name else '')
			c.line(start_pos_left,pos_inicial-2,552,pos_inicial-2)
			
			#for line in item.id_type_line:
			for line in item.calculator_id.line_ids:
				c.setFont("Calibri", 8)
				pagina, pos_inicial = self.verify_linea_op(c,wReal,hReal,pos_inicial,12,pagina,start_pos_left)

				tmp_pos = start_pos_left + 60 #para que sea mas a la derecha
				c.drawString(tmp_pos+2, pos_inicial,line.crystal_num)
				tmp_pos += size_widths[0]
				c.drawString(tmp_pos+2, pos_inicial,line.measures)
				tmp_pos += size_widths[1]
				c.drawString(tmp_pos+27, pos_inicial,line.descuadre or '')
				tmp_pos += size_widths[2]
				c.drawString(tmp_pos-28, pos_inicial,str(line.page_number) or '')
				c.drawString(tmp_pos+6, pos_inicial,'X' if line.polished_id else '')

				tmp_pos += size_widths[3]
				c.drawString(tmp_pos+6, pos_inicial, str(line.entalle) if line.entalle else '')
				tmp_pos += size_widths[4]
				c.drawString(tmp_pos+6, pos_inicial,'X' if line.template else '')
				tmp_pos += size_widths[5]
				c.drawString(tmp_pos+6, pos_inicial,'X' if line.arenado else '')
				tmp_pos += size_widths[6]
				c.drawString(tmp_pos+6, pos_inicial,'X' if line.packed else '')
				tmp_pos += size_widths[7] + size_widths[8]
				
				area = line.area or 0
				c.drawRightString(tmp_pos-2, pos_inicial, '{:,.4f}'.format(decimal.Decimal ("%0.4f" % area)))
				aux_array[0] = tmp_pos-2
				tmp_pos += size_widths[9]
				totals[0] += area

				weight = weight_pro * area
				c.drawRightString(tmp_pos-2, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % weight)))
				aux_array[1] = tmp_pos-2
				totals[1] += weight

				qty_cristales += line.quantity

				#print vertical lines:
				aux = start_pos_left+60
				for x in size_widths:
					c.line(aux,pos_inicial+10,aux,pos_inicial-2)
					aux += x
				c.line(aux,pos_inicial+10,aux,pos_inicial-2)
			
			c.line(start_pos_left+60,pos_inicial-2,552,pos_inicial-2)
			c.drawString(start_pos_left+60, pos_inicial-12, 'Nro. de Piezas: '+str(qty_cristales))
			c.drawRightString(aux_array[0], pos_inicial-12, '{:,.4f}'.format(decimal.Decimal ("%0.4f" % totals[0])))
			c.drawRightString(aux_array[1], pos_inicial-12, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % totals[1])))
			totals = [0,0,0,0]
			qty_cristales = 0

		now = fields.Datetime.context_timestamp(self,datetime.now())
		c.drawString(start_pos_left+10, pos_inicial-48,'Usuario: %s %s'%(self.env.user.name,str(now)[:19]))
		c.save()
		with open(path,'rb') as file:
			export = self.env['export.file.manager'].create({
				'file_name': file_name,
				'file': base64.b64encode(file.read()),	
			})
		return export.export_file(clear=True,path=path)

	# cabezera_op para el segundo reporte
	@api.multi
	def cabezera_op(self,c,wReal,hReal,start_pos_left,size_widths=None):
		try:
			company = self.env['res.company'].search([],limit=1)[0]
		except IndexError:
			raise exceptions.Warning(u"No se creado compañía alguna.\n Configure los datos de su compañía para poder mostrarlos en este reporte.")
		
		if company.logo:
			file = base64.b64decode(company.logo)
			c.drawImage(ImageReader(StringIO.StringIO(file)),start_pos_left,792,width=75,height=40,mask=None)
		else:
			c.setFont("Calibri", 12)
			c.drawString(start_pos_left,800,company.name if company.name else 'Company')

		invoice = ''
		if self.invoice_ids:
			invoice = self.invoice_ids[0].number or ''

		# Datos de Conpañía para la cabecera
		c.setFont("Calibri", 6)
		c.drawString(start_pos_left,784,company.street if company.street else u'Address')
		c.drawString(start_pos_left,778,u'Teféfono: '+company.phone if company.phone else 'no disponible')
		c.drawString(start_pos_left+70,778,u'Fax: '+company.fax if company.fax else 'no disponible')
		c.drawString(start_pos_left,770,company.website or '')
		c.drawString(start_pos_left+100,770,company.email or '')
		ruc = company.partner_id.nro_documento if company.partner_id.nro_documento else ''
		c.drawString(start_pos_left,762,'RUC: '+str(ruc))		
		
		pos_inicial = hReal-83
		posicion_indice = 1
		c.roundRect(375,750,205,50,5)
		c.setFont("Calibri", 13)
		c.drawString( 410 , 785,u'ORDEN DE PRODUCCIÓN')
		c.drawString( 470 , 765, self.name)
		for i in range(0,2):
			c.line(start_pos_left,750-i,365,750-i)
		c.line(start_pos_left,745,365,745)
		c.setFont("Calibri", 8) 
		c.drawString(start_pos_left,730,'Documento:')
		c.drawString(start_pos_left+70,730,invoice)
		c.drawString(start_pos_left,722,'Cliente:')
		c.drawString(start_pos_left+70,722,self.partner_id.name)
		c.drawString(start_pos_left,714,'Obra:')
		c.drawString(start_pos_left+70,714, self.obra or '')
		c.drawString(start_pos_left,706,'Direccion:')
		street   = self.partner_id.street or ''
		street = street.strip()
		province = self.partner_id.province_id.name or ''
		district = self.partner_id.district_id.name or ''
		street  += '/'+province+'/'+district
		c.drawString(start_pos_left+70,706,street)
		c.drawString(start_pos_left,698,'Pto.Llegada:')
		llegada   = self.sale_order_id.partner_shipping_id.street or ''
		llegada = llegada.strip()
		province  = self.sale_order_id.partner_shipping_id.province_id.name or ''
		district  = self.sale_order_id.partner_shipping_id.district_id.name or ''
		llegada  += '/'+province+'/'+district
		c.drawString(start_pos_left+70,698,llegada)	
		c.drawString( 380 ,722,u'Fecha Emisión:')
		c.drawString( 450 ,722,self.date_sale_order)
		c.drawString( 380 ,714,'Fecha Entrega:')
		c.drawString( 450 ,714,self.date_delivery)
		c.drawString( 380 ,706,'Vendedor:')
		c.drawString( 450 ,706,self.seller_id.partner_id.name)
		c.line(start_pos_left,690,580,690)
		
		c.line(80,680,550,680)
		c.line(80,600,550,600)

		c.line(80,680,80,600)
		c.line(150,680,150,600)
		c.line(254,680,254,600)
		c.line(332,680,332,600)
		c.line(410,680,410,600)
		c.line(480,680,480,600)
		c.line(550,680,550,600)
		c.drawString( 90 ,640,'Nro. Cristal')
		c.drawString( 175 ,640,'Medidas (mm)')
		c.drawString( 300 ,640,'Nro.')
		c.drawString( 300 ,630,'Pag.')
		c.drawString( 430 ,640,'Metros')
		c.drawString( 427 ,630,'Cuadrados')
		c.drawString( 495 ,640,'Peso (Kg.)')
		c.rotate(90)
		c.drawString(22*cm, -10*cm, "Descuadre")
		c.drawString(22*cm, -12.3*cm, "Pulido")
		c.drawString(22*cm, -12.8*cm, "Entalle")
		c.drawString(22*cm, -13.3*cm, "Plantilla")
		c.drawString(22*cm, -13.8*cm, "Arenado")
		c.drawString(22*cm, -14.3*cm, "Embalado")
		c.rotate(-90)

	@api.multi
	def verify_linea_op(self,c,wReal,hReal,posactual,valor,pagina,start_pos_left):
		if posactual <40:
			c.showPage()
			self.cabezera_op(c,wReal,hReal,start_pos_left)
			c.setFont("Calibri-Bold", 8)
			return pagina+1,hReal-217
		else:
			return pagina,posactual-valor
	