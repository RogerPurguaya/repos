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
import calendar

def dig_5(n):
	return ("%5d" % n).replace(' ','0')

class grupo_report_extraccion(models.Model):
	_name = 'grupo.report.extraccion'

	titulo = fields.Char('Name',required=True)
	order = fields.Integer('Order',required=True)

	@api.one
	def get_name_person(self):
		self.name = str(self.order) + '-' + self.titulo

	name = fields.Char('Name',compute="get_name_person")


class tipo_report_extraccion(models.Model):
	_name = 'tipo.report.extraccion'

	titulo = fields.Char('Name',required=True)
	order = fields.Integer('Order',required=True)

	@api.one
	def get_name_person(self):
		self.name = str(self.order) + '-' + self.titulo

	name = fields.Char('Name',compute="get_name_person")


class rm_report_extraccion_line(models.Model):
	_name = 'rm.report.extraccion.line'


	rm_report_extraccion_id = fields.Many2one('rm.report.extraccion','Cabezera')

		

	cuenta = fields.Char('Cuenta')
	tipo = fields.Many2one('tipo.report.extraccion','Tipo',required=True)
	concepto = fields.Char('Concepto',required=True)
	grupo = fields.Many2one('grupo.report.extraccion','Grupo',required=True)
	pie_pagina = fields.Selection( [('explosivo','Explosivo'),('laboratorio','Laboratorio'),('depreciacion',u'Depreciación')],'Pie de Página' )
	codigo_rel = fields.Char(u'Código')
	

	enero = fields.Float('Enero',digits=(12,2),readonly=True,default=0)
	febrero = fields.Float('Febrero',digits=(12,2),readonly=True,default=0)
	marzo = fields.Float('Marzo',digits=(12,2),readonly=True,default=0)
	abril = fields.Float('Abril',digits=(12,2),readonly=True,default=0)
	mayo = fields.Float('Mayo',digits=(12,2),readonly=True,default=0)
	junio = fields.Float('Junio',digits=(12,2),readonly=True,default=0)
	julio = fields.Float('Julio',digits=(12,2),readonly=True,default=0)
	agosto = fields.Float('Agosto',digits=(12,2),readonly=True,default=0)
	septiembre = fields.Float('Septiembre',digits=(12,2),readonly=True,default=0)
	octubre = fields.Float('Octubre',digits=(12,2),readonly=True,default=0)
	noviembre = fields.Float('Noviembre',digits=(12,2),readonly=True,default=0)
	diciembre = fields.Float('Diciembre',digits=(12,2),readonly=True,default=0)

	@api.one
	def get_monto(self):
		m = str(self.rm_report_extraccion_id.period_actual.code).split('/')
		m = int(m[0])
		mont = 0
		cant = {
			1: self.enero,
			2: self.febrero,
			3: self.marzo,
			4: self.abril,
			5: self.mayo,
			6: self.junio,
			7: self.julio,
			8: self.agosto,
			9: self.septiembre,
			10: self.octubre,
			11: self.noviembre,
			12: self.diciembre,
		}
		mont = cant[int(self.rm_report_extraccion_id.period_actual.code.split('/')[0])]
		self.monto = mont
	monto = fields.Float('Monto', digits=(12,2), readonly=True, default=0, compute="get_monto")

	@api.one
	def get_acumulado(self):
		self.acumulado = self.enero + self.febrero + self.marzo + self.abril + self.mayo + self.junio + self.julio + self.agosto + self.septiembre + self.octubre + self.noviembre + self.diciembre
	acumulado = fields.Float('Acumulado', readonly=True, default=0, compute="get_acumulado")

	@api.one
	def get_acumulado_pciento(self):
		if self.acumulado != 0:
			self.acumulado_pciento = self.acumulado / self.rm_report_extraccion_id.total_general
		else:
			self.acumulado_pciento = 0
	acumulado_pciento = fields.Float('%  ACUM', readonly=True, compute="get_acumulado_pciento")

	@api.one
	def get_promedio(self):
		if self.acumulado != 0:
			self.promedio = self.acumulado / 1
		else:
			self.promedio = 0
	promedio = fields.Float('Promedio', readonly=True, compute="get_promedio")

	@api.one
	def get_promedio_pciento(self):
		if self.acumulado != 0:
			self.promedio_pciento = self.promedio / self.rm_report_extraccion_id.total_promedio_general
		else:
			self.promedio_pciento = 0
	promedio_pciento = fields.Float('%  PROM', readonly=True, compute="get_promedio_pciento")



class rm_report_extraccion(models.Model):
	_name= 'rm.report.extraccion'

	fiscal = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)
	sitio = fields.Char('Sitio',required=False)
	centro_de_costo = fields.Char('Centro de Costo',readonly=True,default='Extracción')
	proposito = fields.Char('Propósito')
	fecha_emision_reporte = fields.Date('Fecha de Emisión del Reporte',required=True)
	usuario = fields.Many2one('res.users','Usuario',readonly=True)
	conf_line_ids = fields.One2many('rm.report.extraccion.line','rm_report_extraccion_id','Lineas de Configuración')
	period_actual = fields.Many2one('account.period','Periodo Actual Informe',required=True)

	@api.one
	def get_total_general(self):
		self.total_general = 0
		for i in self.conf_line_ids:
			self.total_general += i.acumulado
		print self.total_general
	total_general = fields.Float('Total general', compute="get_total_general")

	@api.one	
	def get_total_promedio_general(self):
		self.total_promedio_general = 0
		for i in self.conf_line_ids:
			self.total_promedio_general += i.promedio
		print self.total_promedio_general
	total_promedio_general = fields.Float('Total general', compute="get_total_promedio_general")

	@api.one
	def unlink(self):
		if len(self.conf_line_ids) > 0:
			raise osv.except_osv('Alerta!', "No se puede eliminar un reporte que contenga lineas.")
		return super(rm_report_extraccion,self).unlink()

	@api.one
	def copy(self,default):
		t= super(rm_report_extraccion,self).copy(default)
		for i in self.conf_line_ids:
			vals_i = {
				'rm_report_extraccion_id':t.id,
				'cuenta':i.cuenta,
				'tipo':i.tipo.id,
				'concepto':i.concepto,
				'grupo':i.grupo.id,
				'enero':0,
				'febrero':0,
				'marzo':0,
				'abril':0,
				'mayo':0,
				'junio':0,
				'julio':0,
				'agosto':0,
				'septiembre':0,
				'octubre':0,
				'noviembre':0,
				'diciembre':0,
				'pie_pagina':i.pie_pagina,
			}
			self.env['rm.report.extraccion.line'].create(vals_i)
		return t

	@api.one
	def get_name_set(self):
		self.name = self.fiscal.name + '-'+ self.centro_de_costo

	name = fields.Char('Nombre',compute='get_name_set')


	@api.model
	def create(self,vals):
		vals['usuario']= self.env.uid
		return super(rm_report_extraccion,self).create(vals)


	@api.one
	def calculate(self):
		m = str(self.period_actual.code).split('/')
		limite = m[1]+ m[0]


		self.env.cr.execute("""
update rm_report_extraccion_line opt set
enero= 0, febrero = 0,
marzo= 0, abril= 0,
mayo= 0, junio= 0,
julio= 0, agosto= 0,
septiembre= 0, octubre= 0,
noviembre= 0, diciembre= 0
where opt.rm_report_extraccion_id = """ + str(self.id) + """
""")


		self.env.cr.execute("""
update rm_report_extraccion_line opt set
enero= saldos.saldo01, febrero = saldos.saldo02,
marzo= saldos.saldo03, abril= saldos.saldo04,
mayo= saldos.saldo05, junio= saldos.saldo06,
julio= saldos.saldo07, agosto= saldos.saldo08,
septiembre= saldos.saldo09, octubre= saldos.saldo10,
noviembre= saldos.saldo11, diciembre= saldos.saldo12
from (
select t1.id,left(t1.code,9)as nivel1,left(t1.code,3) as nivel2,left(t1.code,6) as nivel3,t1.code,t1.name,t1.type,
coalesce(saldo01,0) as saldo01,coalesce(saldo02,0) as saldo02,coalesce(saldo03,0) as saldo03,coalesce(saldo04,0) as saldo04,
coalesce(saldo05,0) as saldo05,coalesce(saldo06,0) as saldo06,coalesce(saldo07,0) as saldo07,coalesce(saldo08,0) as saldo08,
coalesce(saldo09,0) as saldo09,coalesce(saldo10,0) as saldo10,coalesce(saldo11,0) as saldo11,coalesce(saldo12,0) as saldo12,
saldo01+saldo02+saldo03+saldo04+saldo05+saldo06+saldo07+saldo08+saldo09+saldo10+saldo11+saldo12 as total from account_account t1
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo01 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '01/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t2 on t2.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo02 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '02/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t3 on t3.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo03 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '03/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t4 on t4.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo04 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '04/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t5 on t5.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo05 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '05/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t6 on t6.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo06 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '06/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t7 on t7.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo07 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '07/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t8 on t8.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo08 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '08/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t9 on t9.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo09 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '09/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t10 on t10.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo10 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '10/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t11 on t11.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo11 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '11/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t12 on t12.cuenta= left(t1.code,9)
left join (select left(aa.code,9) as cuenta,sum(debit)-sum(credit) as saldo12 from account_move_line aml inner join account_move am on am.id = aml.move_id inner join account_account aa on aa.id = aml.account_id inner join account_period ap on ap.id = am.period_id and ap.date_stop <= '""" +str(self.period_actual.date_stop)+ """'::date and ap.code = '12/""" +str(self.period_actual.code).split('/')[1]+ """' where am.state != 'draft' group by left(aa.code,9)) t13 on t13.cuenta= left(t1.code,9)
where t1.type<>'view') saldos
where opt.cuenta = saldos.nivel1 and opt.rm_report_extraccion_id = """ + str(self.id) + """
			""")

	@api.one
	def get_pie_pagina(self):
		cp_obj = self.env['costos.produccion'].search( [('periodo','=',self.period_actual.id)] )
		rpt = []
		if len(cp_obj) >0:
			cp_obj = cp_obj[0]		
			#### la primera linea
			rpt.append([0,0,0,0,0,0])
			rpt.append([ cp_obj.extra_pro_ton, cp_obj.extra_pro_cp , cp_obj.extra_pro_imp , 0,0,0])
			rpt.append([ cp_obj.extra_ini_ton, cp_obj.extra_ini_cp , cp_obj.extra_ini_imp , 0,0,0])
			rpt.append([0,0,0,0,0,0])
			rpt.append([ cp_obj.extra_dis_ton, cp_obj.extra_dis_cp , cp_obj.extra_dis_imp , 0,0,0])
			rpt.append([0,0,0,0,0,0])
			rpt.append([ cp_obj.extra_tt_ton, cp_obj.extra_tt_cp , cp_obj.extra_tt_imp , 0,0,0])
			rpt.append([0,0,0,0,0,0])
			rpt.append([0,0,0,0,0,0])
			rpt.append([0,0,0,0,0,0])
			rpt.append([0,0,0,0,0,0])
			rpt.append([ cp_obj.extra_final_ton, cp_obj.extra_final_cp , cp_obj.extra_final_imp , 0,0,0])
			
		else:
			for i in range(0,12):
				rpt.append([0,0,0,0,0,0])


		period_list = []
		nro_act = 1
		period_act =  ("%2d"%nro_act).replace(' ','0') +  '/' + self.period_actual.code.split('/')[1]
		nro_act = 2
		mkmk = self.env['account.period'].search( [('code','=',period_act)] )
		if len(mkmk)>0:
			period_list.append(mkmk[0])

		while period_act != self.period_actual.code:
			period_act =  ("%2d"%nro_act).replace(' ','0') +  '/' + self.period_actual.code.split('/')[1]
			nro_act += 1
			mkmk = self.env['account.period'].search( [('code','=',period_act)] )
			if len(mkmk)>0:
				period_list.append(mkmk[0])

		for i in period_list:
			cp_obj = self.env['costos.produccion'].search( [('periodo','=',i.id)] )
			if len(cp_obj) >0:
				cp_obj = cp_obj[0]		
				#### Aqui toda actualizar valores no modificarlos y  ahi sacar el promedio del medio con eso se termina ejemplo
				rpt[1][3] += cp_obj.extra_pro_ton
				rpt[1][5] += cp_obj.extra_pro_imp
				rpt[1][4] = 0 if rpt[1][3] == 0 else (rpt[1][5] / rpt[1][3] )

				if i.code.split('/')[0] == '01':
					rpt[2][3] += cp_obj.extra_ini_ton
					rpt[2][5] += cp_obj.extra_ini_imp
					rpt[2][4] = 0 if rpt[2][3] == 0 else (rpt[2][5] / rpt[2][3] )

				rpt[4][3] = rpt[1][3] + rpt[2][3]
				rpt[4][5] = rpt[1][5] + rpt[2][5]
				rpt[4][4] = 0 if rpt[4][3] == 0 else (rpt[4][5] / rpt[4][3] )

				rpt[6][3] += cp_obj.extra_tt_ton
				rpt[6][5] += cp_obj.extra_tt_imp
				rpt[6][4] = 0 if rpt[6][3] == 0 else (rpt[6][5] / rpt[6][3] )


				rpt[11][3] = rpt[4][3] - rpt[6][3]
				rpt[11][5] = rpt[4][5] - rpt[6][5]
				rpt[11][4] = 0 if rpt[11][3] == 0 else (rpt[11][5] / rpt[11][3] )



		return rpt


	@api.one
	def get_valores(self):


		rpt = []
		periodos = []
		ini = '01/' + self.period_actual.code.split('/')[1]
		periodos.append( self.env['account.period'].search( [('code','=',ini)] )[0] )
		pos = 2

		while ini != self.period_actual.code:
			ini = ('%2d'%pos).replace(' ','0') + '/' + self.period_actual.code.split('/')[1]
			pos += 1
			periodos.append( self.env['account.period'].search( [('code','=',ini)] )[0] )

		for i in periodos:
			cp_obj = self.env['costos.produccion'].search( [('periodo','=',i.id)] )
			if len(cp_obj) >0:
				cp_obj = cp_obj[0]		
				#### la primera linea
				rpt.append( cp_obj.extra_pro_ton )
				
			else:
				rpt.append( 0 )

		for i in range(pos,13):
			rpt.append ( 0 )

		rpt = [rpt]
		rpt.append ([0,0,0,0,0,0,0,0,0,0,0,0] )
		rpt.append ([0,0,0,0,0,0,0,0,0,0,0,0] )
		rpt.append ([0,0,0,0,0,0,0,0,0,0,0,0] )
		rpt.append ([0,0,0,0,0,0,0,0,0,0,0,0] )
		rpt.append ([0,0,0,0,0,0,0,0,0,0,0,0] )

		return rpt


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
			'output_name': 'Reportes Mexicanos Extraccion.pdf',
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
	def cabezera(self,c,wReal,hReal,flag=True):
		pagina = 1
		adicional = 20
		pos_inicial = hReal-30

		c.drawImage( 'calidra.jpg' , 55,pos_inicial-50)
		c.setFont("Arimo-Bold", 11)
		c.setFillColor(black)
		c.drawString( 404 + adicional, pos_inicial, "ANEXO DE OPERACIÓN {0}".format(self.fiscal.name))
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)
		c.drawString( 404 + adicional, pos_inicial, "Sitio:")
		c.setFont("Arimo-Regular", 11)
		c.drawString( 599 + adicional, pos_inicial, self.sitio if self.sitio else '')
		c.setFont("Arimo-Bold", 11)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)
		c.drawString( 404 + adicional, pos_inicial, "Centro de Costo:")
		c.setFont("Arimo-Regular", 11)
		c.drawString( 599 + adicional, pos_inicial, self.centro_de_costo if self.centro_de_costo else '')
		c.setFont("Arimo-Bold", 11)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)
		c.drawString( 404 + adicional, pos_inicial, "Propósito:")
		c.setFont("Arimo-Regular", 11)
		c.drawString( 599 + adicional, pos_inicial, self.proposito if self.proposito else '')
		c.setFont("Arimo-Bold", 11)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)
		c.drawString( 404 + adicional, pos_inicial, "Fecha de Emisión del Reporte:")
		c.setFont("Arimo-Regular", 11)
		c.drawString( 599 + adicional, pos_inicial, self.fecha_emision_reporte if self.fecha_emision_reporte else '')
		c.setFont("Arimo-Bold", 11)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)
		c.drawString( 404 + adicional, pos_inicial, "Usuario:")
		c.setFont("Arimo-Regular", 11)
		c.drawString( 599 + adicional, pos_inicial, self.usuario.name if self.usuario.name else '')

		if flag == True:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,40,pagina)
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

		else:

			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,52,pagina,False)

			c.setFillColor("#CCCCFF")
			c.rect(0+adicional, pos_inicial-8, 591, 44, stroke=1, fill=1)
			ad = 8
			c.line(528 + adicional, pos_inicial-ad, 528 + adicional , pos_inicial + 14)
			c.line(465 + adicional, pos_inicial-ad, 465 + adicional , pos_inicial + 14)
			c.line(402 + adicional, pos_inicial-ad, 402 + adicional , pos_inicial + 35)
			c.line(339 + adicional, pos_inicial-ad, 339 + adicional , pos_inicial + 14)
			c.line(276 + adicional, pos_inicial-ad, 276 + adicional , pos_inicial + 14)
			c.line(213 + adicional, pos_inicial-ad, 213 + adicional , pos_inicial + 35)
			c.line(213 + adicional, pos_inicial-ad +22, 591 + adicional , pos_inicial - ad+22)
			c.setFont("Arimo-Regular", 8)
			c.setFillColor(black)
			c.drawCentredString(106 + adicional,pos_inicial + 14, "CONCEPTO")
			c.drawCentredString(309 + adicional,pos_inicial + 23, "MES ACTUAL")
			c.drawCentredString(498 + adicional,pos_inicial + 23, "ACUMULADO")
			c.drawCentredString(246 + adicional,pos_inicial, "TONS")
			c.drawCentredString(309 + adicional,pos_inicial, "PROMEDIO")
			c.drawCentredString(372 + adicional,pos_inicial, "IMPORTE")
			c.drawCentredString(435 + adicional,pos_inicial, "TONS")
			c.drawCentredString(498 + adicional,pos_inicial, "PROMEDIO")
			c.drawCentredString(561 + adicional,pos_inicial, "IMPORTE")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina,False)

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
		pos_inicial = hReal-162

		pagina = 1
		textPos = 0

		adicional = 20
		
		self.cabezera(c,wReal,hReal)			
		

		
		#print dig_5(self.conf_line_ids[0].tipo.order)+dig_5(self.conf_line_ids[0].grupo.order)
		elements = self.env['rm.report.extraccion.line'].search([('rm_report_extraccion_id','=',self.id)]).sorted(key=lambda r: dig_5(r.tipo.order)+dig_5(r.grupo.order))
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
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,44,pagina)

		if pos_inicial > 202:
			pass
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,202,pagina)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)

		c.setFont("Arimo-Bold", 14)
		c.drawString( 3 + adicional, pos_inicial, "Otros Datos Informativos")
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,30,pagina)

		nombres = ["TONELADAS PRODUCIDAS","COSTO PROCESO POR TONELADA", "COSTO POR TONELADA SIN EXPLOSIVOS", "COSTO DE EXPLOSIVOS", "COSTO LABORATORIO POR TON.", u"COSTO POR TON. SIN DEPRECIACIÓN"]
		valores = [[0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0]]
		valores = self.get_valores()[0]
		for k in range(12):
			if valores[0][k] == 0:
				valores[1][k] = 0
				valores[2][k] = 0
				valores[3][k] = 0
				valores[4][k] = 0
				valores[5][k] = 0
			else:
				valores[1][k] = tot_tot_tot[k] / valores[0][k]
				valores[2][k] = (tot_tot_tot[k] - valores[6][k])/valores[0][k]
				valores[3][k] = valores[6][k] / valores[0][k]
				valores[4][k] = valores[7][k] / valores[0][k]
				valores[5][k] = (tot_tot_tot[k] - (valores[8][k] + valores[9][k] + valores[10][k]))/valores[0][k]



		for i in range(0,6):	
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
			c.setFont("Arimo-Regular", 8)
			c.setFillColor(black)
			c.drawString( 5 + adicional , pos_inicial, nombres[i])
			c.drawRightString( 275 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][0])))
			c.drawRightString( 338 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][1])))
			c.drawRightString( 401 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][2])))
			c.drawRightString( 464 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][3])))
			c.drawRightString( 527 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][4])))
			c.drawRightString( 590 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][5])))
			c.drawRightString( 653 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][6])))
			c.drawRightString( 716 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][7])))
			c.drawRightString( 779 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][8])))
			c.drawRightString( 842 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][9])))
			c.drawRightString( 905 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][10])))
			c.drawRightString( 968 + adicional, pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%.2f"%valores[i][11])))
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina)

		# PIE DE PAGINA
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,30,pagina,False)
		c.setFont("Arimo-Bold", 14)
		c.drawString( 3 + adicional, pos_inicial, "Pie de Página")
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,40,pagina,False)

		c.setFillColor("#CCCCFF")
		c.rect(0+adicional, pos_inicial-8, 591, 44, stroke=1, fill=1)
		ad = 8
		c.line(528 + adicional, pos_inicial-ad, 528 + adicional , pos_inicial + 14)
		c.line(465 + adicional, pos_inicial-ad, 465 + adicional , pos_inicial + 14)
		c.line(402 + adicional, pos_inicial-ad, 402 + adicional , pos_inicial + 35)
		c.line(339 + adicional, pos_inicial-ad, 339 + adicional , pos_inicial + 14)
		c.line(276 + adicional, pos_inicial-ad, 276 + adicional , pos_inicial + 14)
		c.line(213 + adicional, pos_inicial-ad, 213 + adicional , pos_inicial + 35)
		c.line(213 + adicional, pos_inicial-ad +22, 591 + adicional , pos_inicial - ad+22)
		c.setFont("Arimo-Regular", 8)
		c.setFillColor(black)
		c.drawCentredString(106 + adicional,pos_inicial + 14, "CONCEPTO")
		c.drawCentredString(309 + adicional,pos_inicial + 23, "MES ACTUAL")
		c.drawCentredString(498 + adicional,pos_inicial + 23, "ACUMULADO")
		c.drawCentredString(246 + adicional,pos_inicial, "TONS")
		c.drawCentredString(309 + adicional,pos_inicial, "PROMEDIO")
		c.drawCentredString(372 + adicional,pos_inicial, "IMPORTE")
		c.drawCentredString(435 + adicional,pos_inicial, "TONS")
		c.drawCentredString(498 + adicional,pos_inicial, "PROMEDIO")
		c.drawCentredString(561 + adicional,pos_inicial, "IMPORTE")
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina,False)

		nombres = ["TRASPASO PROCESO ANTERIOR","PRODUCCION COSTO POR TONELADA","INVENTARIO INICIAL","COMPRAS","DISPONIBLE","ENVIO TR","TRASPASO A TRITURACION","TRASPASO A AGREGADOS","VENTAS","AJUSTE DE INVENTARIO","OTRAS SALIDAS","INVENTARIO FINAL"]
		
		data_final_pagina = self.get_pie_pagina()[0]

		for i in range(12):	
			c.setFillColor(white, alpha=1)
			c.rect(0+adicional, pos_inicial-8, 591 , 22, stroke=1, fill=1)
			ad = 8
			c.line(528 + adicional, pos_inicial-ad, 528 + adicional , pos_inicial + 14)
			c.line(465 + adicional, pos_inicial-ad, 465 + adicional , pos_inicial + 14)
			c.line(402 + adicional, pos_inicial-ad, 402 + adicional , pos_inicial + 14)
			c.line(339 + adicional, pos_inicial-ad, 339 + adicional , pos_inicial + 14)
			c.line(276 + adicional, pos_inicial-ad, 276 + adicional , pos_inicial + 14)
			c.line(213 + adicional, pos_inicial-ad, 213 + adicional , pos_inicial + 14)
			c.setFont("Arimo-Regular", 8)
			c.setFillColor(black)


			c.drawRightString(528+60 + adicional ,pos_inicial,  '{:,.2f}'.format(decimal.Decimal ("%.2f"%data_final_pagina[i][5])))
			c.drawRightString(528+60 - (63*1) + adicional,pos_inicial,  '{:,.2f}'.format(decimal.Decimal ("%.2f"%data_final_pagina[i][4])))
			c.drawRightString(528+60 - (63*2) + adicional,pos_inicial,  '{:,.2f}'.format(decimal.Decimal ("%.2f"%data_final_pagina[i][3])))
			c.drawRightString(528+60 - (63*3) + adicional,pos_inicial,  '{:,.2f}'.format(decimal.Decimal ("%.2f"%data_final_pagina[i][2])))
			c.drawRightString(528+60 - (63*4) + adicional,pos_inicial,  '{:,.2f}'.format(decimal.Decimal ("%.2f"%data_final_pagina[i][1])))
			c.drawRightString(528+60 - (63*5) + adicional,pos_inicial,  '{:,.2f}'.format(decimal.Decimal ("%.2f"%data_final_pagina[i][0])))

			c.drawString( 5 + adicional , pos_inicial, nombres[i])
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,22,pagina,False)


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
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,flag = True):
		if posactual <65:
			c.showPage()
			self.cabezera(c,wReal,hReal,flag)

			c.setFont("Arimo-Bold", 10)
			#c.drawCentredString(300,25,'Pag. ' + str(pagina+1))
			if flag == True:
				return pagina+1,hReal-162
			else:
				return pagina+1,hReal-174
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

		workbook = Workbook(direccion +'Reporte_Extracción.xlsx')
		worksheet = workbook.add_worksheet(u"Extracción")
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

		numberdoscon = workbook.add_format({'num_format':'#,##0.00'})

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
		worksheet.write(6,8, 'Usuario:', bold)
		worksheet.write(6,12, self.usuario.name if self.usuario.name else '', normal)

		colum = {
			1: "Enero",
			2: "Febrero",
			3: "Marzo",
			4: "Abril",
			5: "Mayo",
			6: "Junio",
			7: "Julio",
			8: "Agosto",
			9: "Septiembre",
			10: "Octubre",
			11: "Noviembre",
			12: "Diciembre",
		}

		worksheet.write(14,0, u'TIPO COSTO', boldbord)
		col = 1
		mon = 0
		while mon+1 <= doce:
			worksheet.write(14,col, u'{0}'.format(colum[mon+1]), boldbord)
			col += 1
			mon += 1
		worksheet.write(14,col, u'Acumulado', boldbord)
		col+=1
		worksheet.write(14,col, u'%  ACUM', boldbord)
		col+=1
		worksheet.write(14,col, u'Promedio', boldbord)
		col+=1
		worksheet.write(14,col, u'%  PROM', boldbord)
		col+=1
		
		elements = self.env['rm.report.extraccion.line'].search([('rm_report_extraccion_id','=',self.id)]).sorted(key=lambda r: dig_5(r.tipo.order)+dig_5(r.grupo.order))
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
				while mon+1 <= doce:
					worksheet.write(x,col, ((sub_tot[mon])), numberdos)
					col += 1
					mon += 1
				worksheet.write(x,col, ((sub_tot[-4])), numberdos)
				col += 1
				worksheet.write(x,col, ((sub_tot[-3])), numberdos)
				col += 1
				worksheet.write(x,col, ((sub_tot[-2])), numberdos)
				col += 1
				worksheet.write(x,col, ((sub_tot[-1])), numberdos)

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

				x += 1
				worksheet.write(x,0, u"TOTAL " + n_tipo.titulo.upper(), boldtotal)
				col = 1
				mon = 0
				while mon+1 <= doce:
					worksheet.write(x,col, ((tot_tot[mon])), numberdos)
					col += 1
					mon += 1
				worksheet.write(x,col, ((tot_tot[-4])), numberdos)
				col += 1
				worksheet.write(x,col, ((tot_tot[-3])), numberdos)
				col += 1
				worksheet.write(x,col, ((tot_tot[-2])), numberdos)
				col += 1
				worksheet.write(x,col, ((tot_tot[-1])), numberdos)
				col += 1

				sub_tot = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				tot_tot = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

				x += 1
				worksheet.write(x,0, u'{0}'.format(i.tipo.titulo), bold)
				x += 1
				worksheet.write(x,0, u'{0}'.format(i.grupo.titulo), bold)
				x += 1
				worksheet.write(x,0, u'{0}'.format(i.concepto), normal)
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
					worksheet.write(x,col, ((mon_m[mon])), numberdoscon)
					col += 1
					mon += 1
				worksheet.write(x,col, ((i.acumulado)), numberdoscon)
				col += 1
				worksheet.write(x,col, ((i.acumulado_pciento)), numberdoscon)
				col += 1
				worksheet.write(x,col, ((i.promedio)), numberdoscon)
				col += 1
				worksheet.write(x,col, ((i.promedio_pciento)), numberdoscon)

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
					worksheet.write(x,col, ((sub_tot[mon])), numberdos)
					col += 1
					mon += 1
				worksheet.write(x,col, ((sub_tot[-4])), numberdos)
				col += 1
				worksheet.write(x,col, ((sub_tot[-3])), numberdos)
				col += 1
				worksheet.write(x,col, ((sub_tot[-2])), numberdos)
				col += 1
				worksheet.write(x,col, ((sub_tot[-1])), numberdos)
				
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
				
				worksheet.write(x,0, u'{0}'.format(i.concepto), normal)
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
					worksheet.write(x,col, ((mon_m[mon])), numberdoscon)
					col += 1
					mon += 1
				worksheet.write(x,col, ((i.acumulado)), numberdoscon)
				col += 1
				worksheet.write(x,col, ((i.acumulado_pciento)), numberdoscon)
				col += 1
				worksheet.write(x,col, ((i.promedio)), numberdoscon)
				col += 1
				worksheet.write(x,col, ((i.promedio_pciento)), numberdoscon)
				
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
				
				worksheet.write(x,0, u'{0}'.format(i.concepto), normal)
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
					worksheet.write(x,col, ((mon_m[mon])), numberdoscon)
					col += 1
					mon += 1
				worksheet.write(x,col, ((i.acumulado)), numberdoscon)
				col += 1
				worksheet.write(x,col, ((i.acumulado_pciento)), numberdoscon)
				col += 1
				worksheet.write(x,col, ((i.promedio)), numberdoscon)
				col += 1
				worksheet.write(x,col, ((i.promedio_pciento)), numberdoscon)
				
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
			worksheet.write(x,col, ((sub_tot[mon])), numberdos)
			col += 1
			mon += 1
		worksheet.write(x,col, ((sub_tot[-4])), numberdos)
		col += 1
		worksheet.write(x,col, ((sub_tot[-3])), numberdos)
		col += 1
		worksheet.write(x,col, ((sub_tot[-2])), numberdos)
		col += 1
		worksheet.write(x,col, ((sub_tot[-1])), numberdos)
		x += 1
		
		#lugar del error:
		#correccion temporal:
		title_tmp = ''
		try:
			title_tmp = n_tipo.titulo.upper()
		except Exception as e:
			print('Error: ',e)
		#title_tmp = n_tipo.titulo.upper() if n_tipo.titulo else ''
		worksheet.write(x,0, u"TOTAL " + title_tmp, boldtotal)

		col = 1
		mon = 0
		while mon+1 <= doce:
			worksheet.write(x,col, ((tot_tot[mon])), numberdos)
			col += 1
			mon += 1
		worksheet.write(x,col, ((tot_tot[-4])), numberdos)
		col += 1
		worksheet.write(x,col, ((tot_tot[-3])), numberdos)
		col += 1
		worksheet.write(x,col, ((tot_tot[-2])), numberdos)
		col += 1
		worksheet.write(x,col, ((tot_tot[-1])), numberdos)
		col += 1
		x += 1

		worksheet.write(x,0, u"COSTO TOTAL DEL PROCESO", boldtotal)
		col = 1
		mon = 0
		while mon+1 <= doce:
			worksheet.write(x,col, ((tot_tot_tot[mon])), numberdos)
			col += 1
			mon += 1
		worksheet.write(x,col, ((tot_tot_tot[-4])), numberdos)
		col += 1
		worksheet.write(x,col, ((tot_tot_tot[-3])), numberdos)
		col += 1
		worksheet.write(x,col, ((tot_tot_tot[-2])), numberdos)
		col += 1
		worksheet.write(x,col, ((tot_tot_tot[-1])), numberdos)
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


		x += 2
		worksheet.write(x,0, u'Otros datos Informativos'.format(i.tipo.titulo), bold)
		x += 1

		nombres = ["TONELADAS PRODUCIDAS","COSTO PROCESO POR TONELADA", "COSTO POR TONELADA SIN EXPLOSIVOS", "COSTO DE EXPLOSIVOS", "COSTO LABORATORIO POR TON.", u"COSTO POR TON. SIN DEPRECIACIÓN"]
		valores = [[0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0]]
		valores = self.get_valores()[0]
		for k in range(12):
			if valores[0][k] == 0:
				valores[1][k] = 0
				valores[2][k] = 0
				valores[3][k] = 0
				valores[4][k] = 0
				valores[5][k] = 0
			else:
				explosivo = self.env['rm.report.extraccion.line'].search( [('rm_report_extraccion_id','=',self.id),('pie_pagina','=','explosivo')] )
				explosivo_val = 0
				if len(explosivo) >0:
					explosivo = explosivo[0]
					if k == 0:
						explosivo_val = explosivo.enero
					elif k== 1:
						explosivo_val = explosivo.febrero
					elif k== 2:
						explosivo_val = explosivo.marzo
					elif k== 3:
						explosivo_val = explosivo.abril
					elif k== 4:
						explosivo_val = explosivo.mayo
					elif k== 5:
						explosivo_val = explosivo.junio
					elif k== 6:
						explosivo_val = explosivo.julio
					elif k== 7:
						explosivo_val = explosivo.agosto
					elif k== 8:
						explosivo_val = explosivo.septiembre
					elif k== 9:
						explosivo_val = explosivo.octubre
					elif k== 10:
						explosivo_val = explosivo.noviembre
					elif k== 11:
						explosivo_val = explosivo.diciembre


				laboratorio = self.env['rm.report.extraccion.line'].search( [('rm_report_extraccion_id','=',self.id),('pie_pagina','=','laboratorio')] )
				laboratorio_val = 0
				if len(laboratorio) >0:
					laboratorio = laboratorio[0]
					if k == 0:
						laboratorio_val = laboratorio.enero
					elif k== 1:
						laboratorio_val = laboratorio.febrero
					elif k== 2:
						laboratorio_val = laboratorio.marzo
					elif k== 3:
						laboratorio_val = laboratorio.abril
					elif k== 4:
						laboratorio_val = laboratorio.mayo
					elif k== 5:
						laboratorio_val = laboratorio.junio
					elif k== 6:
						laboratorio_val = laboratorio.julio
					elif k== 7:
						laboratorio_val = laboratorio.agosto
					elif k== 8:
						laboratorio_val = laboratorio.septiembre
					elif k== 9:
						laboratorio_val = laboratorio.octubre
					elif k== 10:
						laboratorio_val = laboratorio.noviembre
					elif k== 11:
						laboratorio_val = laboratorio.diciembre


				depreciacion = self.env['rm.report.extraccion.line'].search( [('rm_report_extraccion_id','=',self.id),('pie_pagina','=','depreciacion')] )
				depreciacion_val = 0
				for dep in depreciacion:
					if k == 0:
						depreciacion_val += dep.enero
					elif k== 1:
						depreciacion_val += dep.febrero
					elif k== 2:
						depreciacion_val += dep.marzo
					elif k== 3:
						depreciacion_val += dep.abril
					elif k== 4:
						depreciacion_val += dep.mayo
					elif k== 5:
						depreciacion_val += dep.junio
					elif k== 6:
						depreciacion_val += dep.julio
					elif k== 7:
						depreciacion_val += dep.agosto
					elif k== 8:
						depreciacion_val += dep.septiembre
					elif k== 9:
						depreciacion_val += dep.octubre
					elif k== 10:
						depreciacion_val += dep.noviembre
					elif k== 11:
						depreciacion_val += dep.diciembre

				valores[1][k] = tot_tot_tot[k] / valores[0][k]
				valores[2][k] = (tot_tot_tot[k] - explosivo_val )/valores[0][k]
				valores[3][k] = explosivo_val / valores[0][k]
				valores[4][k] = laboratorio_val / valores[0][k]
				valores[5][k] = (tot_tot_tot[k] - (depreciacion_val))/valores[0][k]

		
		worksheet.write(x,0, u'CONCEPTO', boldbord)
		col = 1
		mon = 0
		while mon+1 <= doce:
			worksheet.write(x,col, u'{0}'.format(colum[mon+1]), boldbord)
			col += 1
			mon += 1

		x += 1


		for i in range(0,6):
			worksheet.write(x,0, u'{0}'.format(nombres[i]), normal)
			col = 1
			mon = 0
			while mon+1 <= doce:
				worksheet.write(x,col, ((valores[i][mon])), numberdoscon)
				col += 1
				mon += 1
			x += 1

		x += 2
		worksheet.write(x,0, u'Pie de Página', bold)
		x += 1
		worksheet.merge_range(x,0,x+1,0, u'CONCEPTO', merge_format)
		worksheet.merge_range(x,1,x,3, u'MES ACTUAL', merge_format)
		worksheet.merge_range(x,4,x,6, u'ACUMULADO', merge_format)
		x += 1
		worksheet.write(x,1, u'TONS', boldbord)
		worksheet.write(x,2, u'PROMEDIO', boldbord)
		worksheet.write(x,3, u'IMPORTE', boldbord)
		worksheet.write(x,4, u'TONS', boldbord)
		worksheet.write(x,5, u'PROMEDIO', boldbord)
		worksheet.write(x,6, u'IMPORTE', boldbord)
		x += 1

		nombres = ["TRASPASO PROCESO ANTERIOR","PRODUCCION COSTO POR TONELADA","INVENTARIO INICIAL","COMPRAS","DISPONIBLE","ENVIO TR","TRASPASO A TRITURACION","TRASPASO A AGREGADOS","VENTAS","AJUSTE DE INVENTARIO","OTRAS SALIDAS","INVENTARIO FINAL"]
		
		data_final_pagina = self.get_pie_pagina()[0]
		print "esto es lo raro",data_final_pagina

		for i in range(12):
			worksheet.write(x,0, nombres[i], normal)
			worksheet.write(x,1, ((data_final_pagina[i][0])), numberdoscon)
			worksheet.write(x,2, ((data_final_pagina[i][1])), numberdoscon)
			worksheet.write(x,3, ((data_final_pagina[i][2])), numberdoscon)
			worksheet.write(x,4, ((data_final_pagina[i][3])), numberdoscon)
			worksheet.write(x,5, ((data_final_pagina[i][4])), numberdoscon)
			worksheet.write(x,6, ((data_final_pagina[i][5])), numberdoscon)
			x += 1

		workbook.close()
		
		f = open(direccion + 'Reporte_Extracción.xlsx', 'rb')
		
		vals = {
			'output_name': 'Reportes_Mexicanos_Extrracción.xlsx',
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


class tmp_consulting_for_this_act(models.Model):
	_name = 'tmp.consulting.for.this.act'
	_auto = False

	def init(self,cr):
		cr.execute(""" 
CREATE OR REPLACE FUNCTION get_reporte_hoja_registro_2(IN has_currency boolean, IN periodo_ini integer, IN periodo_fin integer)
  RETURNS TABLE(id bigint, cuenta character varying, descripcion character varying, debe numeric, haber numeric, saldodeudor numeric, saldoacredor numeric, activo numeric, pasivo numeric, perdidasnat numeric, ganancianat numeric, perdidasfun numeric, gananciafun numeric, cuentaf character varying, totaldebe numeric, totalhaber numeric, finaldeudor numeric, finalacreedor numeric) AS
$BODY$
BEGIN

IF $3 is Null THEN
		$3 := $2;
END IF;

RETURN QUERY 
select X.id,X.cuenta,X.descripcion,X.debe,X.haber,X.saldodeudor,X.saldoacredor,
CASE WHEN ((X.activo >0 or X.pasivo >0) or (X.ver_pas=1) ) and X.finaldeudor>0 THEN X.finaldeudor ELSE 0 end activo,
CASE WHEN ((X.pasivo >0 or X.activo >0) or (X.ver_pas=1) ) and X.finalacreedor>0 THEN X.finalacreedor ELSE 0 end pasivo,
CASE WHEN ((X.perdidasnat >0 or X.ganancianat >0) or (X.ver_nat=1) ) and X.finaldeudor>0 THEN X.finaldeudor  ELSE 0 end perdidasnat,
CASE WHEN ((X.ganancianat >0 or X.perdidasnat >0) or (X.ver_nat=1) ) and X.finalacreedor>0 THEN X.finalacreedor ELSE 0 end ganancianat,
CASE WHEN ((X.perdidasfun >0 or X.gananciafun >0) or (X.ver_fun=1) ) and X.finaldeudor >0 THEN X.finaldeudor ELSE 0 end perdidasfun,
CASE WHEN ((X.gananciafun >0 or X.perdidasfun >0) or (X.ver_fun=1) ) and X.finalacreedor>0 THEN X.finalacreedor ELSE 0 end gananciafun,
X.cuentaf,X.totaldebe,X.totalhaber,X.finaldeudor,X.finalacreedor

 from (select row_number() OVER () AS id,RES.* from 
  (select  CASE WHEN M.cuenta IS NOT NULL THEN M.cuenta ELSE aa_f.code END as cuenta, CASE WHEN M.descripcion IS NOT NULL THEN M.descripcion ELSE aa_f.name END as descripcion, M.debe, M.haber, M.saldodeudor, M.saldoacredor, M.activo, M.pasivo, M.perdidasnat, M.ganancianat, M.perdidasfun, M.gananciafun,T.cuentaF, T.totaldebe,T.totalhaber ,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0) >0 THEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0) ELSE 0 END as finaldeudor,
CASE WHEN coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0) <0 THEN -1 * (coalesce(T.totaldebe,0) - coalesce(T.totalhaber,0) + coalesce(M.debe,0) - coalesce(M.haber,0)) ELSE 0 END as finalacreedor,
T.ver_pas, T.ver_nat, T.ver_fun
from get_hoja_trabajo_detalle_registro($1,$2,$3) AS M 
FULL JOIN (select O1.cuenta as cuentaF,
--sum(O1.saldodeudor) as totaldebe,
--sum(O1.saldoacredor) as totalhaber   from get_hoja_trabajo_detalle_registro($1,(substring($2::varchar,0,5)||'00')::integer,(substring($2::varchar,0,5)||'00')::integer ) as O1
sum(O1.debe) as totaldebe,
sum(O1.haber) as totalhaber,
CASE WHEN sum(O1.activo)> 0 or sum(O1.pasivo) >0 THEN 1 ELSE 0 END as ver_pas,
CASE WHEN sum(O1.perdidasnat)> 0 or sum(O1.ganancianat) >0 THEN 1 ELSE 0 END as ver_nat,
CASE WHEN sum(O1.perdidasfun)> 0 or sum(O1.gananciafun) >0 THEN 1 ELSE 0 END as ver_fun

   from get_hoja_trabajo_detalle_registro($1,(substring($2::varchar,0,5)||'00')::integer,(substring($2::varchar,0,5)||'00')::integer ) as O1
group by O1.cuenta) AS T on T.cuentaF = M.cuenta 
left join account_account aa_f on aa_f.code = T.cuentaF order by cuenta) RES) AS X;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
  """)