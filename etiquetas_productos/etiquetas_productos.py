# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from odoo import models, fields, api, exceptions
import codecs,pprint
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
from reportlab.lib.units import inch, cm
import decimal
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128

class GlassFurnaceOut(models.Model):
	_inherit='glass.furnace.out'
	@api.multi
	def print_labels(self):
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
		pdfmetrics.registerFont(TTFont('Calibri-Bold', 'CalibriBold.ttf'))

		path = self.env['main.parameter'].search([])[0].dir_create_file+'etiquetas_cristales.pdf'
		separator = 10
		pos = 95
		pos_left = 8
		width_page,height_page = 7.62 * cm , 5.08 * cm # 216 144
		c = canvas.Canvas(path, pagesize=(width_page,height_page)) 
		lines = self.line_ids.filtered(lambda x: not x.is_break and not x.etiqueta)
		if len(lines) == 0:
			raise exceptions.Warning('No hay cristales pendientes para etiquetar')
		for line in lines:
			c.setFont("Calibri", 10)
			c.drawString(pos_left,pos,'O/P')
			c.setFont("Calibri-Bold", 9)
			c.drawString(pos_left+20,pos,line.lot_line_id.order_prod_id.name)
			c.drawString(pos_left+150,pos,line.lot_line_id.measures)
			c.setFont("Calibri", 10)
			pos -= separator
			c.drawString(pos_left,pos,'Cristal Nro.')
			c.drawString(pos_left+50,pos,line.crystal_number)
			c.setFont("Calibri", 7)
			pos -= separator
			c.drawString(pos_left,pos,line.lot_id.product_id.name or '')
			c.setFont("Calibri-Bold", 10)
			pos -= separator
			c.drawString(pos_left,pos,line.partner_id.name[:40] if line.partner_id.name else '')
			c.setFont("Calibri", 10)
			pos -= separator
			c.drawString(pos_left,pos,line.partner_id.street or '')
			pos -= separator+6
			width_rec = 180
			d1 = self.name
			d2 = line.lot_line_id.calc_line_id.polished_id.code or ''
			d3 = 'E' if line.lot_line_id.calc_line_id.entalle else ''
			d4 = 'PL' if line.lot_line_id.calc_line_id.template else ''
			d5 = 'EM' if line.lot_line_id.calc_line_id.packed else ''
			d6 = '' # pendiente
			data = [d1,d2,d3,d4,d5,d6]
			c.setFont("Calibri", 9)
			inter = int(width_rec/len(data))
			aux = (width_page/2)-(width_rec/2)
			for item in data:
				c.drawCentredString(aux+inter/2,pos+3,item)
				c.rect(aux, pos, inter, 12, stroke=1, fill=0)
				aux+=inter
			pos -= separator
			string = line.lot_line_id.search_code
			c.drawCentredString((width_page/2),pos,string)
			story=[]
			st = code128.Code128(string,barHeight=.32*inch,barWidth=1.2)
			story.append(st)
			st.drawOn(c,10,4)
			pos = 95
			c.showPage()
		c.save()
		file = open(path, 'rb').read()
		export = self.env['export.file.manager'].create({
			'file_name': 'etiquetas_cristales.pdf',
			'file': base64.b64encode(file),	
		})
		lines.write({'etiqueta':True})
		return export.export_file(clear=True,path=path)
