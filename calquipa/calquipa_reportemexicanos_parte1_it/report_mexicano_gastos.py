# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black, white, blue, gray, Color, HexColor, PCMYKColor, PCMYKColorSep
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, legal
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
from cgi import escape

import decimal

def dig_5(n):
	return ("%5d" % n).replace(' ','0')

class grupo_report_gastos(models.Model):
	_name = 'grupo.report.gastos'

	titulo = fields.Char('Name',required=True)
	order = fields.Integer('Order',required=True)

	@api.one
	def get_name_person(self):
		self.name = str(self.order) + '-' + self.titulo

	name = fields.Char('Name',compute="get_name_person")


class tipo_report_gastos(models.Model):
	_name = 'tipo.report.gastos'

	titulo = fields.Char('Name',required=True)
	order = fields.Integer('Order',required=True)

	@api.one
	def get_name_person(self):
		self.name = str(self.order) + '-' + self.titulo

	name = fields.Char('Name',compute="get_name_person")


class rm_report_gastos_line(models.Model):
	_name = 'rm.report.gastos.line'


	rm_report_gastos_id = fields.Many2one('rm.report.gastos','Cabezera')

		

	cuenta = fields.Char('Cuenta',required=False)
	tipo = fields.Many2one('tipo.report.gastos','Tipo',required=True)
	concepto = fields.Char('Concepto',required=True)
	grupo = fields.Many2one('grupo.report.gastos','Grupo',required=True)

	mes_monto = fields.Float('Mes',digits=(12,2),readonly=True,default=0)
	mes_monto_dolares = fields.Float('Mes (dolares)',digits=(12,2),readonly=True,default=0)
	


class rm_report_gastos(models.Model):
	_name= 'rm.report.gastos'

	fiscal = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)
	sitio = fields.Char('Sitio',required=False)
	centro_de_costo = fields.Char('Centro de Costo',readonly=True,default='Gastos')
	proposito = fields.Char('Propósito')
	fecha_emision_reporte = fields.Date('Fecha de Emisión del Reporte',required=True)
	usuario = fields.Many2one('res.users','Usuario',readonly=True)
	conf_line_ids = fields.One2many('rm.report.gastos.line','rm_report_gastos_id','Lineas de Configuración')
	period_actual = fields.Many2one('account.period','Periodo Actual Informe',required=True)
	tipo_cambio = fields.Float('Tipo Cambio',digits=(12,3))


	@api.one
	def unlink(self):
		if len(self.conf_line_ids) > 0:
			raise osv.except_osv('Alerta!', "No se puede eliminar un reporte que contenga lineas.")
		return super(rm_report_gastos,self).unlink()

	@api.one
	def copy(self,default):
		t= super(rm_report_gastos,self).copy(default)
		for i in self.conf_line_ids:
			vals_i = {
				'rm_report_gastos_id':t.id,
				'cuenta':i.cuenta,
				'tipo':i.tipo.id,
				'concepto':i.concepto,
				'grupo':i.grupo.id,
				'mes_monto':0,
				'mes_monto_dolares':0,
			}
			self.env['rm.report.gastos.line'].create(vals_i)
		return t

	@api.one
	def get_name_set(self):
		self.name = self.fiscal.name

	name = fields.Char('Nombre',compute='get_name_set')


	@api.model
	def create(self,vals):
		vals['usuario']= self.env.uid
		return super(rm_report_gastos,self).create(vals)


	@api.one
	def calculate(self):
		m = str(self.period_actual.code).split('/')
		limite = m[1]+ m[0]



		self.env.cr.execute("""
update rm_report_gastos_line opt set
mes_monto= 0, mes_monto_dolares = 0
where opt.rm_report_gastos_id = """ + str(self.id) + """
""")


		self.env.cr.execute("""
update rm_report_gastos_line opt set
mes_monto= saldos.saldo01, mes_monto_dolares = saldos.saldo01 * """ + "%.3f"%self.tipo_cambio + """
from (
select t1.id,left(t1.code,9)as nivel1,left(t1.code,3) as nivel2,left(t1.code,6) as nivel3,t1.code,t1.name,t1.type,
coalesce(saldo01,0) as saldo01
from account_account t1
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo01 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '""" +str(self.period_actual.code)+ """' where am.state != 'draft' group by left(aa.code,9)) t2 on t2.cuenta= left(t1.code,9)
where t1.type<>'view') saldos
where opt.cuenta = saldos.nivel1 and opt.rm_report_gastos_id = """ + str(self.id) + """
			""")


	""" ----------------------------- REPORTE PDF ----------------------------- """

	@api.multi
	def export_pdf(self):
		self.reporteador()
		
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		import os
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		vals = {
			'output_name': 'Reportes Mexicanos Administracion.pdf',
			'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
		}
		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	@api.multi
	def cabezera(self,c,wReal,hReal):
		pagina = 1
		adicional = 20
		pos_inicial = hReal-30

		c.drawImage( 'calquipa.jpg' , 70 ,pos_inicial-60,width=214, height=131)
		c.setFont("Arimo-Bold", 20)
		c.setFillColor(black)
		c.drawString( 404 + adicional, pos_inicial, "CALQUIPA SAC")
		c.setFont("Arimo-Bold", 11)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,30,pagina)
		c.drawString( 404 + adicional, pos_inicial, "ANALÍTICO DE GASTOS DE OPERACIÓN")
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,55,pagina)

		c.setStrokeColor(black)
		c.setFillColor("#CCCCFF")
		c.rect(0+adicional, pos_inicial, 968 , 22, stroke=1, fill=1)
		c.line(906 + adicional, pos_inicial, 906 + adicional , pos_inicial + 22)
		c.line(843 + adicional, pos_inicial, 843 + adicional , pos_inicial + 22)
		c.line(780 + adicional, pos_inicial, 780 + adicional , pos_inicial + 22)
		c.line(717 + adicional, pos_inicial, 717 + adicional , pos_inicial + 22)
		c.line(654 + adicional, pos_inicial, 654 + adicional , pos_inicial + 22)
		c.line(591 + adicional, pos_inicial, 591 + adicional , pos_inicial + 22)
		c.line(528 + adicional, pos_inicial, 528 + adicional , pos_inicial + 22)
		c.line(465 + adicional, pos_inicial, 465 + adicional , pos_inicial + 22)
		c.line(402 + adicional, pos_inicial, 402 + adicional , pos_inicial + 22)
		c.line(339 + adicional, pos_inicial, 339 + adicional , pos_inicial + 22)
		c.line(276 + adicional, pos_inicial, 276 + adicional , pos_inicial + 22)
		c.line(213 + adicional, pos_inicial, 213 + adicional , pos_inicial + 22)
		#c.line(145 + adicional, pos_inicial, 145 + adicional , pos_inicial + 22)
		c.setFillColor(black)
		c.setFont("Arimo-BoldItalic", 9)
		c.drawCentredString(106 + adicional,pos_inicial + 9, "TIPO COSTO")
		c.drawCentredString(246 + adicional,pos_inicial + 9, "Enero")
		c.drawCentredString(309 + adicional,pos_inicial + 9, "Febrero")
		c.drawCentredString(372 + adicional,pos_inicial + 9, "Marzo")
		c.drawCentredString(435 + adicional,pos_inicial + 9, "Abril")
		c.drawCentredString(498 + adicional,pos_inicial + 9, "Mayo")
		c.drawCentredString(561 + adicional,pos_inicial + 9, "Junio")
		c.drawCentredString(624 + adicional,pos_inicial + 9, "Julio")
		c.drawCentredString(687 + adicional,pos_inicial + 9, "Agosto")
		c.drawCentredString(750 + adicional,pos_inicial + 9, "Septiembre")
		c.drawCentredString(813 + adicional,pos_inicial + 9, "Octubre")
		c.drawCentredString(876 + adicional,pos_inicial + 9, "Noviembre")
		c.drawCentredString(939 + adicional,pos_inicial + 9, "Diciembre")

		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)
		#c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		#c.drawCentredString((wReal/2)+20,hReal-96, "LIQUIDACION DE BENEFICIOS SOCIALES")

	@api.multi
	def reporteador(self):

		import sys

		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = legal  # 595 , 842
		#print legal
		wReal = height- 30
		hReal = width - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "a.pdf", pagesize=(height, width))


		pdfmetrics.registerFont(TTFont('Arimo-Bold', 'Arimo-Bold.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-BoldItalic', 'Arimo-BoldItalic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Italic', 'Arimo-Italic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Regular', 'Arimo-Regular.ttf'))

		inicio = 0
		pos_inicial = hReal-132

		pagina = 1
		textPos = 0

		adicional = 20
		
		self.cabezera(c,wReal,hReal)			
		

		
		#print dig_5(self.conf_line_ids[0].tipo.order)+dig_5(self.conf_line_ids[0].grupo.order)
		elements = self.env['rm.report.gastos.line'].search([('rm_report_gastos_id','=',self.id)]).sorted(key=lambda r: dig_5(r.tipo.order)+dig_5(r.grupo.order))
		flag = True
		n_grupo = None
		n_tipo = None
		ultimo_elem = None

		sub_tot = [0,0,0,0,0,0,0,0,0,0,0,0]
		tot_tot = [0,0,0,0,0,0,0,0,0,0,0,0]
		tot_tot_tot = [0,0,0,0,0,0,0,0,0,0,0,0]
		for i in elements:
			if n_tipo == None:
				n_tipo = i.tipo
				c.setFont("Arimo-Bold", 14)
				c.drawString( 3 + adicional, pos_inicial,i.tipo.titulo)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)
			if n_grupo == None:
				n_grupo = i.grupo
				c.setFont("Arimo-Bold", 11)
				c.drawString( 22 + adicional, pos_inicial, i.grupo.titulo)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)

			if n_tipo != i.tipo:
				c.setFont("Arimo-Bold", 9)


				c.drawRightString( 172 + adicional, pos_inicial, "SUB TOTAL")
				c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[0])))
				c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[1])))
				c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[2])))
				c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[3])))
				c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[4])))
				c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[5])))
				c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[6])))
				c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[7])))
				c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[8])))
				c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[9])))
				c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[10])))
				c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[11])))
				tot_tot[0] += sub_tot[0]
				tot_tot[1] += sub_tot[1]
				tot_tot[2] += sub_tot[2]
				tot_tot[3] += sub_tot[3]
				tot_tot[4] += sub_tot[4]
				tot_tot[5] += sub_tot[5]
				tot_tot[6] += sub_tot[6]
				tot_tot[7] += sub_tot[7]
				tot_tot[8] += sub_tot[8]
				tot_tot[9] += sub_tot[9]
				tot_tot[10] += sub_tot[10]
				tot_tot[11] += sub_tot[11]
				tot_tot_tot[0] += tot_tot[0]
				tot_tot_tot[1] += tot_tot[1]
				tot_tot_tot[2] += tot_tot[2]
				tot_tot_tot[3] += tot_tot[3]
				tot_tot_tot[4] += tot_tot[4]
				tot_tot_tot[5] += tot_tot[5]
				tot_tot_tot[6] += tot_tot[6]
				tot_tot_tot[7] += tot_tot[7]
				tot_tot_tot[8] += tot_tot[8]
				tot_tot_tot[9] += tot_tot[9]
				tot_tot_tot[10] += tot_tot[10]
				tot_tot_tot[11] += tot_tot[11]
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)
				c.line(212 + adicional, pos_inicial+10, 968 + adicional , pos_inicial+10)
				c.drawRightString( 172 + adicional, pos_inicial, "TOTAL " + n_tipo.titulo.upper())
				c.line(212 + adicional, pos_inicial-5, 968 + adicional , pos_inicial-5)
				c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[0])))
				c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[1])))
				c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[2])))
				c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[3])))
				c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[4])))
				c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[5])))
				c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[6])))
				c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[7])))
				c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[8])))
				c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[9])))
				c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[10])))
				c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[11])))
				sub_tot = [0,0,0,0,0,0,0,0,0,0,0,0]
				tot_tot = [0,0,0,0,0,0,0,0,0,0,0,0]
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)
				c.setFont("Arimo-Bold", 14)
				c.drawString( 3 + adicional, pos_inicial, i.tipo.titulo)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)
				c.setFont("Arimo-Bold", 11)
				c.drawString( 22 + adicional, pos_inicial, i.grupo.titulo)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)
				c.setFont("Arimo-Regular", 11)
				c.setFillColor(white, alpha=1)
				c.rect(0+adicional, pos_inicial-8, 968 , 22, stroke=1, fill=1)
				c.line(906 + adicional, pos_inicial-ad, 906 + adicional , pos_inicial + 14)
				c.line(843 + adicional, pos_inicial-ad, 843 + adicional , pos_inicial + 14)
				c.line(780 + adicional, pos_inicial-ad, 780 + adicional , pos_inicial + 14)
				c.line(717 + adicional, pos_inicial-ad, 717 + adicional , pos_inicial + 14)
				c.line(654 + adicional, pos_inicial-ad, 654 + adicional , pos_inicial + 14)
				c.line(591 + adicional, pos_inicial-ad, 591 + adicional , pos_inicial + 14)
				c.line(528 + adicional, pos_inicial-ad, 528 + adicional , pos_inicial + 14)
				c.line(465 + adicional, pos_inicial-ad, 465 + adicional , pos_inicial + 14)
				c.line(402 + adicional, pos_inicial-ad, 402 + adicional , pos_inicial + 14)
				c.line(339 + adicional, pos_inicial-ad, 339 + adicional , pos_inicial + 14)
				c.line(276 + adicional, pos_inicial-ad, 276 + adicional , pos_inicial + 14)
				c.line(213 + adicional, pos_inicial-ad, 213 + adicional , pos_inicial + 14)
				#c.line(145 + adicional, pos_inicial-ad, 145 + adicional , pos_inicial + 14)
				c.setFillColor(black)
				c.setFont("Arimo-Regular", 9)
				c.drawString( 3 + adicional, pos_inicial, self.particionar_text(i.concepto) )
				#c.drawString( 147 + adicional, pos_inicial, i.cuenta.code)
				c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.enero)))
				c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.febrero)))
				c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.marzo)))
				c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.abril)))
				c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.mayo)))
				c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.junio)))
				c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.julio)))
				c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.agosto)))
				c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.septiembre)))
				c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.octubre)))
				c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.noviembre)))
				c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.diciembre)))
				sub_tot[0] += i.enero
				sub_tot[1] += i.febrero
				sub_tot[2] += i.marzo
				sub_tot[3] += i.abril
				sub_tot[4] += i.mayo
				sub_tot[5] += i.junio
				sub_tot[6] += i.julio
				sub_tot[7] += i.agosto
				sub_tot[8] += i.septiembre
				sub_tot[9] += i.octubre
				sub_tot[10] += i.noviembre
				sub_tot[11] += i.diciembre
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)
				n_grupo = i.grupo
				n_tipo = i.tipo
			elif n_grupo != i.grupo:
				c.setFont("Arimo-Bold", 9)
				c.drawRightString( 172 + adicional, pos_inicial, "SUB TOTAL")
				c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[0])))
				c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[1])))
				c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[2])))
				c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[3])))
				c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[4])))
				c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[5])))
				c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[6])))
				c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[7])))
				c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[8])))
				c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[9])))
				c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[10])))
				c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[11])))
				tot_tot[0] += sub_tot[0]
				tot_tot[1] += sub_tot[1]
				tot_tot[2] += sub_tot[2]
				tot_tot[3] += sub_tot[3]
				tot_tot[4] += sub_tot[4]
				tot_tot[5] += sub_tot[5]
				tot_tot[6] += sub_tot[6]
				tot_tot[7] += sub_tot[7]
				tot_tot[8] += sub_tot[8]
				tot_tot[9] += sub_tot[9]
				tot_tot[10] += sub_tot[10]
				tot_tot[11] += sub_tot[11]
				sub_tot = [0,0,0,0,0,0,0,0,0,0,0,0]
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)
				c.setFont("Arimo-Bold", 11)
				c.drawString( 22 + adicional, pos_inicial, i.grupo.titulo)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)
				c.setFont("Arimo-Regular", 9)
				c.setFillColor(white, alpha=1)
				c.rect(0+adicional, pos_inicial-8, 968 , 22, stroke=1, fill=1)
				c.line(906 + adicional, pos_inicial-ad, 906 + adicional , pos_inicial + 14)
				c.line(843 + adicional, pos_inicial-ad, 843 + adicional , pos_inicial + 14)
				c.line(780 + adicional, pos_inicial-ad, 780 + adicional , pos_inicial + 14)
				c.line(717 + adicional, pos_inicial-ad, 717 + adicional , pos_inicial + 14)
				c.line(654 + adicional, pos_inicial-ad, 654 + adicional , pos_inicial + 14)
				c.line(591 + adicional, pos_inicial-ad, 591 + adicional , pos_inicial + 14)
				c.line(528 + adicional, pos_inicial-ad, 528 + adicional , pos_inicial + 14)
				c.line(465 + adicional, pos_inicial-ad, 465 + adicional , pos_inicial + 14)
				c.line(402 + adicional, pos_inicial-ad, 402 + adicional , pos_inicial + 14)
				c.line(339 + adicional, pos_inicial-ad, 339 + adicional , pos_inicial + 14)
				c.line(276 + adicional, pos_inicial-ad, 276 + adicional , pos_inicial + 14)
				c.line(213 + adicional, pos_inicial-ad, 213 + adicional , pos_inicial + 14)
				#c.line(145 + adicional, pos_inicial-ad, 145 + adicional , pos_inicial + 14)
				c.setFillColor(black)
				c.drawString( 3 + adicional, pos_inicial, self.particionar_text(i.concepto) )
				#c.drawString( 147 + adicional, pos_inicial, i.cuenta.code)
				c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.enero)))
				c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.febrero)))
				c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.marzo)))
				c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.abril)))
				c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.mayo)))
				c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.junio)))
				c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.julio)))
				c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.agosto)))
				c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.septiembre)))
				c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.octubre)))
				c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.noviembre)))
				c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.diciembre)))
				sub_tot[0] += i.enero
				sub_tot[1] += i.febrero
				sub_tot[2] += i.marzo
				sub_tot[3] += i.abril
				sub_tot[4] += i.mayo
				sub_tot[5] += i.junio
				sub_tot[6] += i.julio
				sub_tot[7] += i.agosto
				sub_tot[8] += i.septiembre
				sub_tot[9] += i.octubre
				sub_tot[10] += i.noviembre
				sub_tot[11] += i.diciembre
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)
				n_grupo = i.grupo
			else:
				c.setFont("Arimo-Regular", 9)
				c.setFillColor(white, alpha=1)
				c.rect(0+adicional, pos_inicial-8, 968 , 22, stroke=1, fill=1)
				ad = 8
				c.line(906 + adicional, pos_inicial-ad, 906 + adicional , pos_inicial + 14)
				c.line(843 + adicional, pos_inicial-ad, 843 + adicional , pos_inicial + 14)
				c.line(780 + adicional, pos_inicial-ad, 780 + adicional , pos_inicial + 14)
				c.line(717 + adicional, pos_inicial-ad, 717 + adicional , pos_inicial + 14)
				c.line(654 + adicional, pos_inicial-ad, 654 + adicional , pos_inicial + 14)
				c.line(591 + adicional, pos_inicial-ad, 591 + adicional , pos_inicial + 14)
				c.line(528 + adicional, pos_inicial-ad, 528 + adicional , pos_inicial + 14)
				c.line(465 + adicional, pos_inicial-ad, 465 + adicional , pos_inicial + 14)
				c.line(402 + adicional, pos_inicial-ad, 402 + adicional , pos_inicial + 14)
				c.line(339 + adicional, pos_inicial-ad, 339 + adicional , pos_inicial + 14)
				c.line(276 + adicional, pos_inicial-ad, 276 + adicional , pos_inicial + 14)
				c.line(213 + adicional, pos_inicial-ad, 213 + adicional , pos_inicial + 14)
				#c.line(145 + adicional, pos_inicial-ad, 145 + adicional , pos_inicial + 14)
				c.setFillColor(black)
				c.drawString( 3 + adicional, pos_inicial, self.particionar_text(i.concepto) )
				#c.drawString( 147 + adicional, pos_inicial, i.cuenta.code)
				c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.enero)))
				c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.febrero)))
				c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.marzo)))
				c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.abril)))
				c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.mayo)))
				c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.junio)))
				c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.julio)))
				c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.agosto)))
				c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.septiembre)))
				c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.octubre)))
				c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.noviembre)))
				c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.diciembre)))
				sub_tot[0] += i.enero
				sub_tot[1] += i.febrero
				sub_tot[2] += i.marzo
				sub_tot[3] += i.abril
				sub_tot[4] += i.mayo
				sub_tot[5] += i.junio
				sub_tot[6] += i.julio
				sub_tot[7] += i.agosto
				sub_tot[8] += i.septiembre
				sub_tot[9] += i.octubre
				sub_tot[10] += i.noviembre
				sub_tot[11] += i.diciembre
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)

			ultimo_elem = i

		tot_tot_tot[0] += tot_tot[0]
		tot_tot_tot[1] += tot_tot[1]
		tot_tot_tot[2] += tot_tot[2]
		tot_tot_tot[3] += tot_tot[3]
		tot_tot_tot[4] += tot_tot[4]
		tot_tot_tot[5] += tot_tot[5]
		tot_tot_tot[6] += tot_tot[6]
		tot_tot_tot[7] += tot_tot[7]
		tot_tot_tot[8] += tot_tot[8]
		tot_tot_tot[9] += tot_tot[9]
		tot_tot_tot[10] += tot_tot[10]
		tot_tot_tot[11] += tot_tot[11]

		c.setFont("Arimo-Bold", 9)
		c.drawRightString( 172 + adicional, pos_inicial, "SUB TOTAL")
		c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[0])))
		c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[1])))
		c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[2])))
		c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[3])))
		c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[4])))
		c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[5])))
		c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[6])))
		c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[7])))
		c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[8])))
		c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[9])))
		c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[10])))
		c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[11])))
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)

		c.line(212 + adicional, pos_inicial+10, 968 + adicional , pos_inicial+10)
		c.drawRightString( 172 + adicional, pos_inicial, "TOTAL " + n_tipo.titulo.upper())
		c.line(212 + adicional, pos_inicial-5, 968 + adicional , pos_inicial-5)
		c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[0])))
		c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[1])))
		c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[2])))
		c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[3])))
		c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[4])))
		c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[5])))
		c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[6])))
		c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[7])))
		c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[8])))
		c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[9])))
		c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[10])))
		c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[11])))
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)

		c.line(212 + adicional, pos_inicial+10, 968 + adicional , pos_inicial+10)
		c.drawRightString( 172 + adicional, pos_inicial, "COSTO TOTAL DEL PROCESO")
		c.line(212 + adicional, pos_inicial-5, 968 + adicional , pos_inicial-5)
		c.line(212 + adicional, pos_inicial-8, 968 + adicional , pos_inicial-8)
		c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[0])))
		c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[1])))
		c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[2])))
		c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[3])))
		c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[4])))
		c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[5])))
		c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[6])))
		c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[7])))
		c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[8])))
		c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[9])))
		c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[10])))
		c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[11])))
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)

		pagina += 1
		c.showPage()

		inicio = 0
		pos_inicial = hReal-94
		pagina = 1
		textPos = 0
		c.save()

	@api.multi
	def particionar_text(self,c):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Arimo-Regular',9,160)
			if len(lines)>1:
				return tet[:-1]
		return tet

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Arimo-Bold", 10)
			#c.drawCentredString(300,25,'Pag. ' + str(pagina+1))
			return pagina+1,hReal-132
		else:
			return pagina,posactual-valor

	""" ----------------------------- REPORTE PDF ----------------------------- """

	""" ----------------------------- REPORTE EXCEL ----------------------------- """

	@api.multi
	def export_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")

		workbook = Workbook(direccion +'Reporte_Administración.xlsx')
		worksheet = workbook.add_worksheet(u"Administración")
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
		numberdos = workbook.add_format({'num_format':'#,##0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)	

		boldtotal = workbook.add_format({'bold': True})
		boldtotal.set_align('right')
		boldtotal.set_align('vright')

		merge_format = workbook.add_format({
											'bold': 1,
											'border': 1,
											'align': 'center',
											'valign': 'vcenter',
											})	
		merge_format.set_bg_color('#DCE6F1')
		merge_format.set_text_wrap()
		merge_format.set_font_size(9)

		m = str(self.period_actual.code).split('/')
		m = int(m[0])
		doce = 12

		worksheet.insert_image('C2', 'calidra.jpg')
		worksheet.write(1,8, u'ANEXO DE OPERACIÓN {0}'.format(self.fiscal.name), bold)
		worksheet.write(2,8, 'Sitio:', bold)
		worksheet.write(2,12, self.sitio if self.sitio else '', normal)
		worksheet.write(3,8, 'Centro de Costo:', bold)
		worksheet.write(3,12, self.centro_de_costo if self.centro_de_costo else '', normal)
		worksheet.write(4,8, u'Propósito:', bold)
		worksheet.write(4,12, self.proposito if self.proposito else '', normal)
		worksheet.write(5,8, u'Fecha de Emisión del Reporte:', bold)
		worksheet.write(5,12, self.fecha_emision_reporte if self.fecha_emision_reporte else '', normal)
		worksheet.write(6,8, u'Tipo de Cambio:', bold)
		worksheet.write(6,12, self.tipo_cambio , numbertres)
		worksheet.write(7,8, 'Usuario:', bold)
		worksheet.write(7,12, self.usuario.name if self.usuario.name else '', normal)



		worksheet.write(14,0, u'TIPO COSTO', boldbord)
		worksheet.write(14,1, u'Mes Monto', boldbord)
		worksheet.write(14,2, u'Mes Monto Dolares', boldbord)
		
		
		elements = self.env['rm.report.gastos.line'].search([('rm_report_gastos_id','=',self.id)]).sorted(key=lambda r: dig_5(r.tipo.order)+dig_5(r.grupo.order))
		flag = True
		n_grupo = None
		n_tipo = None
		ultimo_elem = None

		sub_tot = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tot_tot = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tot_tot_tot = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		x= 15
		for i in elements:
			if n_tipo == None:
				n_tipo = i.tipo
				worksheet.write(x,0, u'{0}'.format(i.tipo.titulo), bold)
				x += 1
			if n_grupo == None:
				n_grupo = i.grupo
				worksheet.write(x,0, u'{0}'.format(i.grupo.titulo), bold)
				x += 1
			if n_tipo != i.tipo:
				worksheet.write(x,0, u'SUB TOTAL', boldtotal)
				col = 1
				mon = 0

				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%self.mes_monto)), numberdos)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%self.mes_monto_dolares)), numberdos)
				col += 1


				tot_tot[0] += sub_tot[0]
				tot_tot[1] += sub_tot[1]
				tot_tot_tot[0] += tot_tot[0]
				tot_tot_tot[1] += tot_tot[1]

				
				x += 1
				worksheet.write(x,0, u"TOTAL " + n_tipo.titulo.upper(), boldtotal)
				col = 1
				mon = 0
				while mon+1 <= doce:
					worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[mon])), numberdos)
					col += 1
					mon += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[-4])), numberdos)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[-3])), numberdos)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[-2])), numberdos)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[-1])), numberdos)
				col += 1

				sub_tot = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				tot_tot = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

				x += 1
				worksheet.write(x,0, u'{0}'.format(i.tipo.titulo), bold)
				x += 1
				worksheet.write(x,0, u'{0}'.format(i.grupo.titulo), bold)
				x += 1
				worksheet.write(x,0, u'{0}'.format(i.concepto), bord)
				mon_m = {
					0: i.enero,
					1: i.febrero,
					2: i.marzo,
					3: i.abril,
					4: i.mayo,
					5: i.junio,
					6: i.julio,
					7: i.agosto,
					8: i.septiembre,
					9: i.octubre,
					10: i.noviembre,
					11: i.diciembre,
				}
				col = 1
				mon = 0
				while mon+1 <= doce:
					worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%mon_m[mon])), bord)
					col += 1
					mon += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.acumulado)), bord)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.acumulado_pciento)), bord)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.promedio)), bord)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.promedio_pciento)), bord)

				sub_tot[0] += i.enero
				sub_tot[1] += i.febrero
				sub_tot[2] += i.marzo
				sub_tot[3] += i.abril
				sub_tot[4] += i.mayo
				sub_tot[5] += i.junio
				sub_tot[6] += i.julio
				sub_tot[7] += i.agosto
				sub_tot[8] += i.septiembre
				sub_tot[9] += i.octubre
				sub_tot[10] += i.noviembre
				sub_tot[11] += i.diciembre
				sub_tot[12] += i.acumulado
				sub_tot[13] += i.acumulado_pciento
				sub_tot[14] += i.promedio
				sub_tot[15] += i.promedio_pciento
				x += 1
				n_grupo = i.grupo
				n_tipo = i.tipo
			elif n_grupo != i.grupo:
				worksheet.write(x,0, u'SUB TOTAL', boldtotal)
				col = 1
				mon = 0
				while mon+1 <= doce:
					worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[mon])), numberdos)
					col += 1
					mon += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[-4])), numberdos)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[-3])), numberdos)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[-2])), numberdos)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[-1])), numberdos)
				
				tot_tot[0] += sub_tot[0]
				tot_tot[1] += sub_tot[1]
				tot_tot[2] += sub_tot[2]
				tot_tot[3] += sub_tot[3]
				tot_tot[4] += sub_tot[4]
				tot_tot[5] += sub_tot[5]
				tot_tot[6] += sub_tot[6]
				tot_tot[7] += sub_tot[7]
				tot_tot[8] += sub_tot[8]
				tot_tot[9] += sub_tot[9]
				tot_tot[10] += sub_tot[10]
				tot_tot[11] += sub_tot[11]
				tot_tot[12] += sub_tot[12]
				tot_tot[13] += sub_tot[13]
				tot_tot[14] += sub_tot[14]
				tot_tot[15] += sub_tot[15]
				sub_tot = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				x += 1
				worksheet.write(x,0, u'{0}'.format(i.grupo.titulo), bold)
				x += 1
				
				worksheet.write(x,0, u'{0}'.format(i.concepto), bord)
				mon_m = {
					0: i.enero,
					1: i.febrero,
					2: i.marzo,
					3: i.abril,
					4: i.mayo,
					5: i.junio,
					6: i.julio,
					7: i.agosto,
					8: i.septiembre,
					9: i.octubre,
					10: i.noviembre,
					11: i.diciembre,
				}
				col = 1
				mon = 0
				while mon+1 <= doce:
					worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%mon_m[mon])), bord)
					col += 1
					mon += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.acumulado)), bord)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.acumulado_pciento)), bord)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.promedio)), bord)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.promedio_pciento)), bord)
				
				sub_tot[0] += i.enero
				sub_tot[1] += i.febrero
				sub_tot[2] += i.marzo
				sub_tot[3] += i.abril
				sub_tot[4] += i.mayo
				sub_tot[5] += i.junio
				sub_tot[6] += i.julio
				sub_tot[7] += i.agosto
				sub_tot[8] += i.septiembre
				sub_tot[9] += i.octubre
				sub_tot[10] += i.noviembre
				sub_tot[11] += i.diciembre
				sub_tot[12] += i.acumulado
				sub_tot[13] += i.acumulado_pciento
				sub_tot[14] += i.promedio
				sub_tot[15] += i.promedio_pciento
				x += 1
				n_grupo = i.grupo
			else:
				
				worksheet.write(x,0, u'{0}'.format(i.concepto), bord)
				mon_m = {
					0: i.enero,
					1: i.febrero,
					2: i.marzo,
					3: i.abril,
					4: i.mayo,
					5: i.junio,
					6: i.julio,
					7: i.agosto,
					8: i.septiembre,
					9: i.octubre,
					10: i.noviembre,
					11: i.diciembre,
				}
				col = 1
				mon = 0
				while mon+1 <= doce:
					worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%mon_m[mon])), bord)
					col += 1
					mon += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.acumulado)), bord)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.acumulado_pciento)), bord)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.promedio)), bord)
				col += 1
				worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%i.promedio_pciento)), bord)
				
				sub_tot[0] += i.enero
				sub_tot[1] += i.febrero
				sub_tot[2] += i.marzo
				sub_tot[3] += i.abril
				sub_tot[4] += i.mayo
				sub_tot[5] += i.junio
				sub_tot[6] += i.julio
				sub_tot[7] += i.agosto
				sub_tot[8] += i.septiembre
				sub_tot[9] += i.octubre
				sub_tot[10] += i.noviembre
				sub_tot[11] += i.diciembre
				sub_tot[12] += i.acumulado
				sub_tot[13] += i.acumulado_pciento
				sub_tot[14] += i.promedio
				sub_tot[15] += i.promedio_pciento
				x += 1

			ultimo_elem = i
			
		tot_tot[0] += sub_tot[0]
		tot_tot[1] += sub_tot[1]
		tot_tot[2] += sub_tot[2]
		tot_tot[3] += sub_tot[3]
		tot_tot[4] += sub_tot[4]
		tot_tot[5] += sub_tot[5]
		tot_tot[6] += sub_tot[6]
		tot_tot[7] += sub_tot[7]
		tot_tot[8] += sub_tot[8]
		tot_tot[9] += sub_tot[9]
		tot_tot[10] += sub_tot[10]
		tot_tot[11] += sub_tot[11]
		tot_tot[12] += sub_tot[12]
		tot_tot[13] += sub_tot[13]
		tot_tot[14] += sub_tot[14]
		tot_tot[15] += sub_tot[15]

		tot_tot_tot[0] += tot_tot[0]
		tot_tot_tot[1] += tot_tot[1]
		tot_tot_tot[2] += tot_tot[2]
		tot_tot_tot[3] += tot_tot[3]
		tot_tot_tot[4] += tot_tot[4]
		tot_tot_tot[5] += tot_tot[5]
		tot_tot_tot[6] += tot_tot[6]
		tot_tot_tot[7] += tot_tot[7]
		tot_tot_tot[8] += tot_tot[8]
		tot_tot_tot[9] += tot_tot[9]
		tot_tot_tot[10] += tot_tot[10]
		tot_tot_tot[11] += tot_tot[11]
		tot_tot_tot[12] += tot_tot[12]
		tot_tot_tot[13] += tot_tot[13]
		tot_tot_tot[14] += tot_tot[14]
		tot_tot_tot[15] += tot_tot[15]

		worksheet.write(x,0, u'SUB TOTAL', boldtotal)
		col = 1
		mon = 0
		while mon+1 <= doce:
			worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[mon])), numberdos)
			col += 1
			mon += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[-4])), numberdos)
		col += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[-3])), numberdos)
		col += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[-2])), numberdos)
		col += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%sub_tot[-1])), numberdos)
		x += 1

		worksheet.write(x,0, u"TOTAL " + n_tipo.titulo.upper(), boldtotal)
		col = 1
		mon = 0
		while mon+1 <= doce:
			worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[mon])), numberdos)
			col += 1
			mon += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[-4])), numberdos)
		col += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[-3])), numberdos)
		col += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[-2])), numberdos)
		col += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot[-1])), numberdos)
		col += 1
		x += 1

		worksheet.write(x,0, u"COSTO TOTAL DEL PROCESO", boldtotal)
		col = 1
		mon = 0
		while mon+1 <= doce:
			worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[mon])), numberdos)
			col += 1
			mon += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[-4])), numberdos)
		col += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[-3])), numberdos)
		col += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[-2])), numberdos)
		col += 1
		worksheet.write(x,col, '{:,.2f}'.format(decimal.Decimal ("%.2f"%tot_tot_tot[-1])), numberdos)
		col += 1
		x += 1

		t = 11.86
		worksheet.set_column('A:A', 49)
		worksheet.set_column('B:B', t)
		worksheet.set_column('C:C', t)
		worksheet.set_column('D:D', t)
		worksheet.set_column('E:E', t)
		worksheet.set_column('F:F', t)
		worksheet.set_column('G:G', t)
		worksheet.set_column('H:H', t)
		worksheet.set_column('I:I', t)
		worksheet.set_column('J:J', t)
		worksheet.set_column('K:K', t)
		worksheet.set_column('L:L', t)
		worksheet.set_column('M:M', t)
		worksheet.set_column('N:N', t)
		worksheet.set_column('O:O', t)
		worksheet.set_column('P:P', t)
		worksheet.set_column('Q:Q', t)

		workbook.close()
		
		f = open(direccion + 'Reporte_Administración.xlsx', 'rb')
		
		vals = {
			'output_name': 'Reportes_Mexicanos_Administración.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	""" ----------------------------- REPORTE EXCEL ----------------------------- """