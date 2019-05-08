# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.osv import osv, expression

from xlsxwriter.workbook import Workbook
import base64
import pprint
import io
import os
import sys


class hr_five_category_import(models.Model):
	_name = 'hr.five.category.import'

	file = fields.Binary('Archivo Importacion')
	mes = fields.Selection([('1','Enero'),('2','Febrero'),('3','Marzo'),('4','Abril'),('5','Mayo'),('6','Junio'),('7','Julio'),('8','Agosto'),('9','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')],'Mes Importacion')
	delimitador = fields.Char('Delimitador',default=';')

	@api.one
	def importar(self):
		datos = base64.decodestring(self.file)
		for i in datos.split('\n'):
			linea = i.split(self.delimitador)
			if len(linea)>=2:
				quinta = self.env['hr.five.category'].browse(self.env.context['active_id'])
				detalle = quinta.line_ids.filtered(lambda l: l.employee_id.identification_id == linea[0])
				if len(detalle)>0:
					detalle = detalle[0]
					if self.mes == '1':
						detalle.janu_amount  = linea[1]
					elif self.mes == '2':
						detalle.febr_amount  = linea[1]
					elif self.mes == '3':
						detalle.marc_amount  = linea[1]
					elif self.mes == '4':
						detalle.apri_amount  = linea[1]
					elif self.mes == '5':
						detalle.mayo_amount  = linea[1]
					elif self.mes == '6':
						detalle.june_amount  = linea[1]
					elif self.mes == '7':
						detalle.july_amount  = linea[1]
					elif self.mes == '8':
						detalle.agos_amount  = linea[1]
					elif self.mes == '9':
						detalle.sept_amount  = linea[1]
					elif self.mes == '10':
						detalle.octo_amount  = linea[1]
					elif self.mes == '11':
						detalle.nove_amount  = linea[1]
					elif self.mes == '12':
						detalle.dece_amount  = linea[1]



class hr_five_category(models.Model):
	_name = 'hr.five.category'
	_rec_name='fiscalyear'
	
	fiscalyear = fields.Many2one('account.fiscalyear','Año fiscal')
	line_ids   = fields.One2many('hr.five.category.lines','five_category_id','Empleados')


	@api.multi
	def importar(self):
		return {
			'name': 'Importacion',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.five.category.import',
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
	
	@api.one
	def procesar(self):
		for line in self.line_ids:
			if line.employee_id.no_domiciliado:
				af = 0
				if line.employee_id.children_number > 0:
					hp = self.env['hr.parameters'].search([('num_tipo','=',10001)])
					af = hp[0].monto

				extraordinary_dict = {
					'01': 0,
					'02': 0,
					'03': 0,
					'04': 0,
					'05': 0,
					'06': 0,
					'07': 0,
					'08': 0,
					'09': 0,
					'10': 0,
					'11': 0,
					'12': 0,
				}

				for extra in line.concept_ids:					
					per = 1
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.january = amount

					per = 2
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.february = amount

					per = 3
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					print period
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					print ht
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					print htl
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					print hcl
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						print amount
						print extra.march
						extra.march = amount
						print extra.march

					per = 4
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.april = amount

					per = 5
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.may = amount

					per = 6
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.june = amount

					per = 7
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.july = amount

					per = 8
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.august = amount

					per = 9
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.september = amount

					per = 10
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.october = amount

					per = 11
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.november = amount

					per = 12
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.december = amount

				for extra in line.concept_ids:
					extraordinary_dict['01'] += extra.january
					extraordinary_dict['02'] += extra.february
					extraordinary_dict['03'] += extra.march
					extraordinary_dict['04'] += extra.april
					extraordinary_dict['05'] += extra.may
					extraordinary_dict['06'] += extra.june
					extraordinary_dict['07'] += extra.july
					extraordinary_dict['08'] += extra.august
					extraordinary_dict['09'] += extra.september
					extraordinary_dict['10'] += extra.october
					extraordinary_dict['11'] += extra.november
					extraordinary_dict['12'] += extra.december
				line.janu_amount = extraordinary_dict['01'] * 30/100.00
				line.febr_amount = extraordinary_dict['02'] * 30/100.00
				line.marc_amount = extraordinary_dict['03'] * 30/100.00
				line.apri_amount = extraordinary_dict['04'] * 30/100.00
				line.mayo_amount = extraordinary_dict['05'] * 30/100.00
				line.june_amount = extraordinary_dict['06'] * 30/100.00
				line.july_amount = extraordinary_dict['07'] * 30/100.00
				line.agos_amount = extraordinary_dict['08'] * 30/100.00
				line.sept_amount = extraordinary_dict['09'] * 30/100.00
				line.octo_amount = extraordinary_dict['10'] * 30/100.00
				line.nove_amount = extraordinary_dict['11'] * 30/100.00
				line.dece_amount = extraordinary_dict['12'] * 30/100.00

				############################
				# PARA LA PESTÑA "CALCULOS"
				############################
				for i in line.calculo_lines:
					i.unlink()

				for extra in line.concept_ids:
					calculo_vals = {
						'five_line_id': line.id,

						'is_red': False,

						'row_text' : extra.concepto_id.name,
						'january'  : extra.january,
						'february' : extra.february,
						'march'    : extra.march,
						'april'    : extra.april,
						'may'      : extra.may,
						'june'     : extra.june,
						'july'     : extra.july,
						'august'   : extra.august,
						'september': extra.september,
						'october'  : extra.october,
						'november' : extra.november,
						'december' : extra.december,
					}
					new_hfcc = self.env['hr.five.category.calculo'].create(calculo_vals)
				
				vals_sum = {
					'five_line_id': line.id,

					'is_red': True,

					'row_text' : 'total',
					'january'  : extraordinary_dict['01'],
					'february' : extraordinary_dict['02'],
					'march'    : extraordinary_dict['03'],
					'april'    : extraordinary_dict['04'],
					'may'      : extraordinary_dict['05'],
					'june'     : extraordinary_dict['06'],
					'july'     : extraordinary_dict['07'],
					'august'   : extraordinary_dict['08'],
					'september': extraordinary_dict['09'],
					'october'  : extraordinary_dict['10'],
					'november' : extraordinary_dict['11'],
					'december' : extraordinary_dict['12'],
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_sum)

				vals_sum = {
					'five_line_id': line.id,

					'is_red': True,

					'row_text' : u'Retención mensual',
					'january'  : line.janu_amount,
					'february' : line.febr_amount,
					'march'    : line.marc_amount,
					'april'    : line.apri_amount,
					'may'      : line.mayo_amount,
					'june'     : line.june_amount,
					'july'     : line.july_amount,
					'august'   : line.agos_amount,
					'september': line.sept_amount,
					'october'  : line.octo_amount,
					'november' : line.nove_amount,
					'december' : line.dece_amount,
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_sum)
				################################
				# FIN PARA LA PESTÑA "CALCULOS"
				################################
			else:
				# PARA LA PESTÑA "CALCULOS"
				for i in line.calculo_lines:
					i.unlink()

				ordinary_dict = {
					'01': 0,
					'02': 0,
					'03': 0,
					'04': 0,
					'05': 0,
					'06': 0,
					'07': 0,
					'08': 0,
					'09': 0,
					'10': 0,
					'11': 0,
					'12': 0,
				}
				intern_dict = {
					'01': 0,
					'02': 0,
					'03': 0,
					'04': 0,
					'05': 0,
					'06': 0,
					'07': 0,
					'08': 0,
					'09': 0,
					'10': 0,
					'11': 0,
					'12': 0,
				}
				extraordinary_dict = {
					'01': 0,
					'02': 0,
					'03': 0,
					'04': 0,
					'05': 0,
					'06': 0,
					'07': 0,
					'08': 0,
					'09': 0,
					'10': 0,
					'11': 0,
					'12': 0,
				}
				total_dict = {
					'01': 0,
					'02': 0,
					'03': 0,
					'04': 0,
					'05': 0,
					'06': 0,
					'07': 0,
					'08': 0,
					'09': 0,
					'10': 0,
					'11': 0,
					'12': 0,
				}

				for ordi in line.line_ids:
					ordinary_dict['01'] += ordi.january * 12
					ordinary_dict['02'] += ordi.february * 11
					ordinary_dict['03'] += ordi.march * 10
					ordinary_dict['04'] += ordi.april * 9
					ordinary_dict['05'] += ordi.may * 8
					ordinary_dict['06'] += ordi.june * 7
					ordinary_dict['07'] += ordi.july * 6
					ordinary_dict['08'] += ordi.august * 5
					ordinary_dict['09'] += ordi.september * 4
					ordinary_dict['10'] += ordi.october * 3
					ordinary_dict['11'] += ordi.november * 2
					ordinary_dict['12'] += ordi.december * 1

					############################
					# PARA LA PESTÑA "CALCULOS"
					############################

					calculo_vals = {
						'five_line_id': line.id,

						'is_red': False,

						'row_text' : ordi.concepto_id.name,
						'january'  : ordi.january,
						'february' : ordi.february,
						'march'    : ordi.march,
						'april'    : ordi.april,
						'may'      : ordi.may,
						'june'     : ordi.june,
						'july'     : ordi.july,
						'august'   : ordi.august,
						'september': ordi.september,
						'october'  : ordi.october,
						'november' : ordi.november,
						'december' : ordi.december,
					}
					new_hfcc = self.env['hr.five.category.calculo'].create(calculo_vals)
					################################
					# FIN PARA LA PESTÑA "CALCULOS"
					################################

				############################
				# PARA LA PESTÑA "CALCULOS"
				############################
				vals_sum = {
					'five_line_id': line.id,

					'is_red': True,

					'row_text' : 'Suma',
					'january'  : ordinary_dict['01']/12,
					'february' : ordinary_dict['02']/11,
					'march'    : ordinary_dict['03']/10,
					'april'    : ordinary_dict['04']/9,
					'may'      : ordinary_dict['05']/8,
					'june'     : ordinary_dict['06']/7,
					'july'     : ordinary_dict['07']/6,
					'august'   : ordinary_dict['08']/5,
					'september': ordinary_dict['09']/4,
					'october'  : ordinary_dict['10']/3,
					'november' : ordinary_dict['11']/2,
					'december' : ordinary_dict['12']/1,
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_sum)

				vals_sum = {
					'five_line_id': line.id,

					'is_red': False,

					'row_text' : 'Meses',
					'january'  : 12,
					'february' : 11,
					'march'    : 10,
					'april'    : 9,
					'may'      : 8,
					'june'     : 7,
					'july'     : 6,
					'august'   : 5,
					'september': 4,
					'october'  : 3,
					'november' : 2,
					'december' : 1,
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_sum)

				vals_sum = {
					'five_line_id': line.id,

					'is_red': True,

					'row_text' : 'Total',
					'january'  : ordinary_dict['01'],
					'february' : ordinary_dict['02'],
					'march'    : ordinary_dict['03'],
					'april'    : ordinary_dict['04'],
					'may'      : ordinary_dict['05'],
					'june'     : ordinary_dict['06'],
					'july'     : ordinary_dict['07'],
					'august'   : ordinary_dict['08'],
					'september': ordinary_dict['09'],
					'october'  : ordinary_dict['10'],
					'november' : ordinary_dict['11'],
					'december' : ordinary_dict['12'],
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_sum)
				################################
				# FIN PARA LA PESTÑA "CALCULOS"
				################################

				for ordi in line.line_ids:
					intern_dict['01'] += (ordi.january * 2)*1.09
					intern_dict['02'] += (ordi.february * 2)*1.09
					intern_dict['03'] += (ordi.march * 2)*1.09
					intern_dict['04'] += (ordi.april * 2)*1.09
					intern_dict['05'] += (ordi.may * 2)*1.09
					intern_dict['06'] += (ordi.june * 2)*1.09
					intern_dict['07'] += (ordi.july * 2)*1.09
					intern_dict['08'] += (ordi.august * 2)*1.09
					intern_dict['09'] += (ordi.september * 2)*1.09
					intern_dict['10'] += (ordi.october * 2)*1.09
					intern_dict['11'] += (ordi.november * 2)*1.09
					intern_dict['12'] += (ordi.december * 2)*1.09

				if line.jul_dic_lines[0].january > 0:
					intern_dict['01'] = line.jul_dic_lines[0].january
				if line.jul_dic_lines[0].february > 0:
					intern_dict['02'] = line.jul_dic_lines[0].february
				if line.jul_dic_lines[0].march > 0:
					intern_dict['03'] = line.jul_dic_lines[0].march
				if line.jul_dic_lines[0].april > 0:
					intern_dict['04'] = line.jul_dic_lines[0].april
				if line.jul_dic_lines[0].may > 0:
					intern_dict['05'] = line.jul_dic_lines[0].may
				if line.jul_dic_lines[0].june > 0:
					intern_dict['06'] = line.jul_dic_lines[0].june
				if line.jul_dic_lines[0].july > 0:
					intern_dict['07'] = line.jul_dic_lines[0].july
				if line.jul_dic_lines[0].august > 0:
					intern_dict['08'] = line.jul_dic_lines[0].august
				if line.jul_dic_lines[0].september > 0:
					intern_dict['09'] = line.jul_dic_lines[0].september
				if line.jul_dic_lines[0].october > 0:
					intern_dict['10'] = line.jul_dic_lines[0].october
				if line.jul_dic_lines[0].november > 0:
					intern_dict['11'] = line.jul_dic_lines[0].november
				if line.jul_dic_lines[0].december > 0:
					intern_dict['12'] = line.jul_dic_lines[0].december

				############################
				# PARA LA PESTÑA "CALCULOS"
				############################
				vals_inte = {
					'five_line_id': line.id,

					'is_red': False,

					'row_text' : 'Grati. Jul y Dic',
					'january'  : intern_dict['01'],
					'february' : intern_dict['02'],
					'march'    : intern_dict['03'],
					'april'    : intern_dict['04'],
					'may'      : intern_dict['05'],
					'june'     : intern_dict['06'],
					'july'     : intern_dict['07'],
					'august'   : intern_dict['08'],
					'september': intern_dict['09'],
					'october'  : intern_dict['10'],
					'november' : intern_dict['11'],
					'december' : intern_dict['12'],
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_inte)
				################################
				# FIN PARA LA PESTÑA "CALCULOS"
				################################

				for extra in line.concept_ids:
					extraordinary_dict['01'] += extra.january

					per = 1
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.february = amount
					# extraordinary_dict['02'] += extra.february

					per = 2
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.march = amount
					# extraordinary_dict['03'] += extra.march

					per = 3
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.april = amount
					# extraordinary_dict['04'] += extra.april

					per = 4
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.may = amount
					# extraordinary_dict['05'] += extra.may

					per = 5
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.june = amount
					# extraordinary_dict['06'] += extra.june

					per = 6
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.july = amount
					# extraordinary_dict['07'] += extra.july

					per = 7
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.august = amount
					# extraordinary_dict['08'] += extra.august

					per = 8
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.september = amount
					# extraordinary_dict['09'] += extra.september

					per = 9
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.october = amount
					# extraordinary_dict['10'] += extra.october

					per = 10
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.november = amount
					# extraordinary_dict['11'] += extra.november

					per = 11
					period = format(per,'02') + "/" + line.five_category_id.fiscalyear.code
					ht = self.env['hr.tareo'].search([('periodo.code','=',period)])
					htl = self.env['hr.tareo.line'].search([('tareo_id','in',ht.ids),('employee_id','=',line.employee_id.id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','in',htl.ids),('concepto_id','=',extra.concepto_id.id)])
					if len(hcl) > 0:
						amount = 0
						for con in hcl:
							amount += con.monto
						extra.december = amount
					# extraordinary_dict['12'] += extra.december

					############################
					# PARA LA PESTÑA "CALCULOS"
					############################

					is_proy=False
					for ld in line.line_ids:
						if ld.concepto_id.id == extra.concepto_id.id:
							is_proy=True
							break
					if is_proy:		
						vals_extra = {
							'five_line_id': line.id,

							'is_red': False,

							'row_text' : extra.concepto_id.name,
							'january'  : extra.january,
								'february' : extra.february,
								'march'    : extra.march+extra.february,
								'april'    : extra.april+extra.march+extra.february,
								'may'      : extra.may+extra.april+extra.march+extra.february,
								'june'     : extra.june+extra.may+extra.april+extra.march+extra.february,
								'july'     : extra.july+extra.june+extra.may+extra.april+extra.march+extra.february,
								'august'   : extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february,
								'september': extra.september+extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february,
								'october'  : extra.october+extra.september+extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february,
								'november' : extra.november+extra.october+extra.september+extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february,
								'december' : extra.december+extra.november+extra.october+extra.september+extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february,
						}
						extraordinary_dict['01']+=extra.january
						extraordinary_dict['02']+=extra.february
						extraordinary_dict['03']+=extra.march+extra.february
						extraordinary_dict['04']+=extra.april+extra.march+extra.february
						extraordinary_dict['05']+=extra.may+extra.april+extra.march+extra.february
						extraordinary_dict['06']+=extra.june+extra.may+extra.april+extra.march+extra.february
						extraordinary_dict['07']+=extra.july+extra.june+extra.may+extra.april+extra.march+extra.february
						extraordinary_dict['08']+=extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february
						extraordinary_dict['09']+=extra.september+extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february
						extraordinary_dict['10']+=extra.october+extra.september+extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february
						extraordinary_dict['11']+=extra.november+extra.october+extra.september+extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february
						extraordinary_dict['12']+=extra.december+extra.november+extra.october+extra.september+extra.august+extra.july+extra.june+extra.may+extra.april+extra.march+extra.february
					else:
						vals_extra = {
							'five_line_id': line.id,
							'is_red': False,
							'row_text' : extra.concepto_id.name,
							'january'  : extra.january,
							'february' : extra.february,
							'march'    : extra.march,
							'april'    : extra.april,
							'may'      : extra.may,
							'june'     : extra.june,
							'july'     : extra.july,
							'august'   : extra.august,
							'september': extra.september,
							'october'  : extra.october,
							'november' : extra.november,
							'december' : extra.december,
						}

						extraordinary_dict['01']+=extra.january
						extraordinary_dict['02']+=extra.february
						extraordinary_dict['03']+=extra.march
						extraordinary_dict['04']+=extra.april
						extraordinary_dict['05']+=extra.may
						extraordinary_dict['06']+=extra.june
						extraordinary_dict['07']+=extra.july
						extraordinary_dict['08']+=extra.august
						extraordinary_dict['09']+=extra.september
						extraordinary_dict['10']+=extra.october
						extraordinary_dict['11']+=extra.november
						extraordinary_dict['12']+=extra.december


					new_hfcc = self.env['hr.five.category.calculo'].create(vals_extra)
					###############################
					# FIN PARA LA PESTÑA "CALCULOS"
					###############################

				lista_meses = ['01','02','03','04','05','06','07','08','09','10','11','12']
				# for cont in range(1,len(lista_meses)):
				# 	extraordinary_dict[lista_meses[cont]] += extraordinary_dict[lista_meses[cont-1]]

				############################
				# PARA LA PESTÑA "CALCULOS"
				############################
				vals_sum = {
					'five_line_id': line.id,

					'is_red': True,

					'row_text' : 'Suma',
					'january'  : extraordinary_dict['01'] + intern_dict['01'] + ordinary_dict['01'],
					'february' : extraordinary_dict['02'] + intern_dict['02'] + ordinary_dict['02'],
					'march'    : extraordinary_dict['03'] + intern_dict['03'] + ordinary_dict['03'],
					'april'    : extraordinary_dict['04'] + intern_dict['04'] + ordinary_dict['04'],
					'may'      : extraordinary_dict['05'] + intern_dict['05'] + ordinary_dict['05'],
					'june'     : extraordinary_dict['06'] + intern_dict['06'] + ordinary_dict['06'],
					'july'     : extraordinary_dict['07'] + intern_dict['07'] + ordinary_dict['07'],
					'august'   : extraordinary_dict['08'] + intern_dict['08'] + ordinary_dict['08'],
					'september': extraordinary_dict['09'] + intern_dict['09'] + ordinary_dict['09'],
					'october'  : extraordinary_dict['10'] + intern_dict['10'] + ordinary_dict['10'],
					'november' : extraordinary_dict['11'] + intern_dict['11'] + ordinary_dict['11'],
					'december' : extraordinary_dict['12'] + intern_dict['12'] + ordinary_dict['12'],
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_sum)
				###############################
				# FIN PARA LA PESTÑA "CALCULOS"
				###############################

				huh = self.env['hr.uit.historical'].search([('fiscalyear_id','=',line.five_category_id.fiscalyear.id)])
				sum_uit = 0
				for uit in huh:
					sum_uit += uit.amount

				############################
				# PARA LA PESTÑA "CALCULOS"
				############################
				vals_sum = {
					'five_line_id': line.id,

					'is_red': False,

					'row_text' : '7 UIT',
					'january'  : sum_uit*7,
					'february' : sum_uit*7,
					'march'    : sum_uit*7,
					'april'    : sum_uit*7,
					'may'      : sum_uit*7,
					'june'     : sum_uit*7,
					'july'     : sum_uit*7,
					'august'   : sum_uit*7,
					'september': sum_uit*7,
					'october'  : sum_uit*7,
					'november' : sum_uit*7,
					'december' : sum_uit*7,
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_sum)
				###############################
				# FIN PARA LA PESTÑA "CALCULOS"
				###############################

				for cont in lista_meses:
					total_dict[cont] = ordinary_dict[cont] + intern_dict[cont] + extraordinary_dict[cont] - (sum_uit*7)

				############################
				# PARA LA PESTÑA "CALCULOS"
				############################
				vals_tot = {
					'five_line_id': line.id,

					'is_red': True,

					'row_text' : 'Total',
					'january'  : total_dict['01'],
					'february' : total_dict['02'],
					'march'    : total_dict['03'],
					'april'    : total_dict['04'],
					'may'      : total_dict['05'],
					'june'     : total_dict['06'],
					'july'     : total_dict['07'],
					'august'   : total_dict['08'],
					'september': total_dict['09'],
					'october'  : total_dict['10'],
					'november' : total_dict['11'],
					'december' : total_dict['12'],
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_tot)
				###############################
				# FIN PARA LA PESTÑA "CALCULOS"
				###############################

				h5 = self.env['hr.5percent'].search([('uit_id.fiscalyear_id','=',self.fiscalyear.id)]).sorted(key=lambda r: r.id)
				h5_tmp = self.env['hr.5percent'].search([('type_element','=','hasta'),('uit_id.fiscalyear_id','=',self.fiscalyear.id)]).sorted(key=lambda r: r.id)

				res = []

				uit_ids_tramos = {} # PARA LA PESTAÑA "CALCULOS"
				uit_ids        = {} # PARA LA PESTAÑA "CALCULOS"

				for cont in lista_meses:
					tmp_res = []
					tmp = total_dict[cont]

					###########################
					# PARA LA PESTÑA "CALCULOS"
					###########################
					for i in h5_tmp:
						if i.type_element+str(i.uit_qty) not in uit_ids_tramos:
							new_hfcc = self.env['hr.five.category.calculo'].create({'five_line_id': line.id, 'is_red': False, 'row_text': (i.type_element+" "+str(i.uit_qty)+" "+"UIT")})
							uit_ids_tramos[i.type_element+str(i.uit_qty)] = new_hfcc
					if h5[-1].type_element+str(h5[-1].uit_qty) not in uit_ids_tramos:
						new_hfcc = self.env['hr.five.category.calculo'].create({'five_line_id': line.id, 'is_red': False, 'row_text': (h5[-1].type_element+" "+str(h5[-1].uit_qty)+" "+"UIT")})
						uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)] = new_hfcc
					###############################
					# FIN PARA LA PESTÑA "CALCULOS"
					###############################

					uit_qty = []
					for i in h5_tmp:
						uit_qty.append(sum_uit*i.uit_qty)
						if i.type_element+str(i.uit_qty) not in uit_ids: # PARA LA PESTAÑA "CALCULOS"
							new_hfcc = self.env['hr.five.category.calculo'].create({'five_line_id': line.id, 'is_red': False, 'row_text': (i.type_element+" "+str(i.uit_qty)+" "+"UIT")})
							uit_ids[i.type_element+str(i.uit_qty)] = new_hfcc

					if h5[-1].type_element+str(h5[-1].uit_qty) not in uit_ids: # PARA LA PESTAÑA "CALCULOS"
						new_hfcc = self.env['hr.five.category.calculo'].create({'five_line_id': line.id, 'is_red': False, 'row_text': (h5[-1].type_element+" "+str(h5[-1].uit_qty)+" "+"UIT")})
						uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)] = new_hfcc

					uit_qty2 = []
					aux = 0
					for i in uit_qty:
						uit_qty2.append(i-aux)
						aux = i

					distrib = []
					for i in uit_qty2:
						if tmp >= i:
							distrib.append(i)
							tmp -= i
						else:
							distrib.append(tmp)
							tmp = 0
							break

					j = 0
					for i in range(len(distrib)):
						tmp_res.append(distrib[i]*h5[j].tasa/100.00)

						###########################
						# PARA LA PESTÑA "CALCULOS" 
						###########################
						if cont == '01':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].january = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].january = distrib[i]
						if cont == '02':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].february = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].february = distrib[i]
						if cont == '03':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].march = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].march = distrib[i]
						if cont == '04':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].april = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].april = distrib[i]
						if cont == '05':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].may = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].may = distrib[i]
						if cont == '06':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].june = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].june = distrib[i]
						if cont == '07':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].july = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].july = distrib[i]
						if cont == '08':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].august = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].august = distrib[i]
						if cont == '09':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].september = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].september = distrib[i]
						if cont == '10':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].october = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].october = distrib[i]
						if cont == '11':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].november = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].november = distrib[i]
						if cont == '12':
							uit_ids[h5[j].type_element+str(h5[j].uit_qty)].december = distrib[i]*h5[j].tasa/100.00
							uit_ids_tramos[h5[j].type_element+str(h5[j].uit_qty)].december = distrib[i]
						###############################
						# FIN PARA LA PESTÑA "CALCULOS"
						###############################
						j += 2
					if tmp != 0:
						tmp_res.append(tmp*h5[-1].tasa/100.00)
						###########################
						# PARA LA PESTÑA "CALCULOS" 
						###########################
						if cont == '01':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].january = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].january = tmp
						if cont == '02':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].february = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].february = tmp
						if cont == '03':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].march = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].march = tmp
						if cont == '04':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].april = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].april = tmp
						if cont == '05':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].may = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].may = tmp
						if cont == '06':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].june = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].june = tmp
						if cont == '07':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].july = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].july = tmp
						if cont == '08':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].august = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].august = tmp
						if cont == '09':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].september = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].september = tmp
						if cont == '10':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].october = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].october = tmp
						if cont == '11':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].november = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].november = tmp
						if cont == '12':
							uit_ids[h5[-1].type_element+str(h5[-1].uit_qty)].december = tmp*h5[-1].tasa/100.00
							uit_ids_tramos[h5[-1].type_element+str(h5[-1].uit_qty)].december = tmp
						###############################
						# FIN PARA LA PESTÑA "CALCULOS"
						###############################
					res.append(sum(tmp_res))

				janu = res[0]/12.00
				febr = res[1]/12.00
				marc = res[2]/12.00
				apri = (res[3] - janu - febr - marc)/9.00
				mayo = (res[4] - janu - febr - marc - apri)/8.00
				june = (res[5] - janu - febr - marc - apri)/8.00
				july = (res[6] - janu - febr - marc - apri)/8.00
				agos = (res[7] - janu - febr - marc - apri - mayo - june - july)/5.00
				sept = (res[8] - janu - febr - marc - apri - mayo - june - july - agos)/4.00
				octo = (res[9] - janu - febr - marc - apri - mayo - june - july - agos)/4.00
				nove = (res[10] - janu - febr - marc - apri - mayo - june - july - agos)/4.00
				dece = (res[11] - janu - febr - marc - apri - mayo - june - july - agos - sept - octo - nove)

				line.janu_amount = janu if janu > 0 else 0
				line.febr_amount = febr if febr > 0 else 0
				line.marc_amount = marc if marc > 0 else 0
				line.apri_amount = apri if apri > 0 else 0
				line.mayo_amount = mayo if mayo > 0 else 0
				line.june_amount = june if june > 0 else 0
				line.july_amount = july if july > 0 else 0
				line.agos_amount = agos if agos > 0 else 0
				line.sept_amount = sept if sept > 0 else 0
				line.octo_amount = octo if octo > 0 else 0
				line.nove_amount = nove if nove > 0 else 0
				line.dece_amount = dece if dece > 0 else 0

				###########################
				# PARA LA PESTÑA "CALCULOS" 
				###########################
				vals_ret = {
					'five_line_id': line.id,

					'is_red': True,

					'row_text' : 'Retenciones de meses anteriores',
					'january'  : 0,
					'february' : 0,
					'march'    : 0,
					'april'    : janu + febr + marc,
					'may'      : janu + febr + marc + apri,
					'june'     : janu + febr + marc + apri,
					'july'     : janu + febr + marc + apri,
					'august'   : janu + febr + marc + apri + mayo + june + july,
					'september': janu + febr + marc + apri + mayo + june + july + agos,
					'october'  : janu + febr + marc + apri + mayo + june + july + agos,
					'november' : janu + febr + marc + apri + mayo + june + july + agos,
					'december' : janu + febr + marc + apri + mayo + june + july + agos + sept + octo + nove,
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_ret)
				vals_ret = {
					'five_line_id': line.id,

					'is_red': True,

					'row_text' : 'Total IR anual proyectado',
					'january'  : janu*12,
					'february' : febr*12,
					'march'    : marc*12,
					'april'    : apri*9,
					'may'      : mayo*8,
					'june'     : june*8,
					'july'     : july*8,
					'august'   : agos*5,
					'september': sept*4,
					'october'  : octo*4,
					'november' : nove*4,
					'december' : dece,
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_ret)
				vals_ret = {
					'five_line_id': line.id,

					'is_red': False,

					'row_text' : 'Factor',
					'january'  : 12,
					'february' : 12,
					'march'    : 12,
					'april'    : 9,
					'may'      : 8,
					'june'     : 8,
					'july'     : 8,
					'august'   : 5,
					'september': 4,
					'october'  : 4,
					'november' : 4,
					'december' : 0,
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_ret)
				vals_sum = {
					'five_line_id': line.id,

					'is_red': True,

					'row_text' : u'Retención mensual',
					'january'  : line.janu_amount,
					'february' : line.febr_amount,
					'march'    : line.marc_amount,
					'april'    : line.apri_amount,
					'may'      : line.mayo_amount,
					'june'     : line.june_amount,
					'july'     : line.july_amount,
					'august'   : line.agos_amount,
					'september': line.sept_amount,
					'october'  : line.octo_amount,
					'november' : line.nove_amount,
					'december' : line.dece_amount,
				}
				new_hfcc = self.env['hr.five.category.calculo'].create(vals_sum)
				###############################
				# FIN PARA LA PESTÑA "CALCULOS"
				###############################

class hr_five_category_lines(models.Model):
	_name = 'hr.five.category.lines'
	_rec_name='employee_id'
	
	five_category_id = fields.Many2one('hr.five.category','Main')

	employee_id = fields.Many2one('hr.employee', 'Trabajador')	
	janu_amount = fields.Float('Enero',digist=(12,2))
	febr_amount = fields.Float('Febrero',digist=(12,2))
	marc_amount = fields.Float('Marzo',digist=(12,2))
	apri_amount = fields.Float('Abril',digist=(12,2))
	mayo_amount = fields.Float('Mayo',digist=(12,2))
	june_amount = fields.Float('Junio',digist=(12,2))
	july_amount = fields.Float('Julio',digist=(12,2))
	agos_amount = fields.Float('Agosto',digist=(12,2))
	sept_amount = fields.Float('Setiembre',digist=(12,2))
	octo_amount = fields.Float('Octubre',digist=(12,2))
	nove_amount = fields.Float('Noviembre',digist=(12,2))
	dece_amount = fields.Float('Diciembre',digist=(12,2))

	line_ids      = fields.One2many('hr.five.category.proy','five_line_id','detalle')
	concept_ids   = fields.One2many('hr.five.category.concepts','five_line_id','detalle conceptos')
	calculo_lines = fields.One2many('hr.five.category.calculo','five_line_id','detalle calculos')
	jul_dic_lines = fields.One2many('hr.five.category.jul.dic','five_line_id','detalle jul dic')

	@api.multi
	def show_detail():
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "hr.five.category.proy",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}

	@api.multi
	def reward_dec(self):
		december_period = self.env['account.period'].search([('code','=','12/'+self.five_category_id.fiscalyear.code)])
		if len(december_period):
			december_period = december_period[0]
			reward_december = self.env['hr.reward.line'].search([('reward.period_id','=',december_period.id),('employee_id','=',self.employee_id.id)])
			if len(reward_december):
				reward_december = reward_december[0]
				self.jul_dic_lines[0].december = reward_december.total*1.09
			else:
				raise osv.except_osv('Alerta!',u"No existe gratificación para el periodo "+december_period.code)
		else:
			raise osv.except_osv('Alerta!',u"No existe periodo "+december_period.code)

	@api.multi
	def reward_jul(self):
		december_period = self.env['account.period'].search([('code','=','06/'+self.five_category_id.fiscalyear.code)])
		if len(december_period):
			december_period = december_period[0]
			reward_december = self.env['hr.reward.line'].search([('reward.period_id','=',december_period.id),('employee_id','=',self.employee_id.id)])
			if len(reward_december):
				reward_december = reward_december[0]
				self.jul_dic_lines[0].july = reward_december.total*1.09
			else:
				raise osv.except_osv('Alerta!',u"No existe gratificación para el periodo "+december_period.code)
		else:
			raise osv.except_osv('Alerta!',u"No existe periodo "+december_period.code)

	@api.multi
	def make_excel(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		basic = {
			'align'		: 'left',
			'valign'	: 'vcenter',
			'text_wrap'	: 1,
			'font_size'	: 9,
			'font_name'	: 'Calibri'
		}

		numeric = basic.copy()
		numeric['align'] = 'right'
		numeric['num_format'] = '#,##0.00'

		numeric_int = basic.copy()
		numeric_int['align'] = 'right'

		numeric_int_bold = numeric.copy()
		numeric_int_bold['bold'] = 1

		numeric_bold = numeric.copy()
		numeric_bold['bold'] = 1
		numeric_bold['num_format'] = '#,##0.00'

		bold = basic.copy()
		bold['bold'] = 1

		header = bold.copy()
		header['bg_color'] = '#A9D0F5'
		header['border'] = 1
		header['align'] = 'center'

		title = bold.copy()
		title['font_size'] = 15

		highlight_line = basic.copy()
		highlight_line['bold'] = 1
		highlight_line['bg_color'] = '#C1E1FF'

		highlight_numeric_line = highlight_line.copy()
		highlight_numeric_line['num_format'] = '#,##0.00'
		highlight_numeric_line['align'] = 'right'		

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		titulo    = u'Reporte_5ta_categoria'
		workbook  = Workbook(direccion + titulo + '.xlsx')

		worksheet = workbook.add_worksheet(self.employee_id.name_related if self.employee_id.name_related else "Empleado")
		
		basic_format                  = workbook.add_format(basic)
		bold_format                   = workbook.add_format(bold)
		numeric_int_format            = workbook.add_format(numeric_int)
		numeric_int_bold_format       = workbook.add_format(numeric_int_bold)
		numeric_format                = workbook.add_format(numeric)
		numeric_bold_format           = workbook.add_format(numeric_bold)
		title_format                  = workbook.add_format(title)
		header_format                 = workbook.add_format(header)
		highlight_line_format         = workbook.add_format(highlight_line)
		highlight_numeric_line_format = workbook.add_format(highlight_numeric_line)

		rc = self.env['res.company'].search([])[0]
		worksheet.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet.merge_range('A2:D2', "RUC: "+rc.partner_id.type_number if rc.partner_id.type_number else 'RUC: ', title_format)
		worksheet.merge_range('A3:D3', ("Trabajador: "+self.employee_id.name_related) if self.employee_id.name_related else "Trabajador", title_format)

		row = 3
		col = 0

		headers = [u'Concepto',
				   u'Enero',
				   u'Febrero',
				   u'Marzo',
				   u'Abril',
				   u'Mayo',
				   u'Junio',
				   u'Julio',
				   u'Agosto',
				   u'Septiembre',
				   u'Octubre',
				   u'Noviembre',
				   u'Diciembre',]

		row += 1
		for pos in range(len(headers)):
			worksheet.write(row,pos, headers[pos], header_format)

		row += 1		
		for line in self.calculo_lines:
			col = 0
			text_line_format = highlight_line_format if line.is_red else basic_format
			numeric_line_format = highlight_numeric_line_format if line.is_red else numeric_format

			worksheet.write(row,col,line.row_text if line.row_text else 0.00, text_line_format)
			col += 1
			worksheet.write(row,col,line.january if line.january else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.february if line.february else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.march if line.march else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.april if line.april else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.may if line.may else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.june if line.june else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.july if line.july else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.august if line.august else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.september if line.september else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.october if line.october else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.november if line.november else 0.00, numeric_line_format)
			col += 1
			worksheet.write(row,col,line.december if line.december else 0.00, numeric_line_format)
			col += 1

			row += 1

		col_sizes = [10.43, 24.71, 41.43]
		worksheet.set_column('A:A', col_sizes[2])
		worksheet.set_column('B:M', col_sizes[0])

		workbook.close()

		f = open(direccion + titulo + '.xlsx', 'rb')
		
		vals = {
			'output_name': titulo + '.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id  = self.env['export.file.save'].create(vals)

		return {
			"type"     : "ir.actions.act_window",
			"res_model": "export.file.save",
			"views"    : [[False, "form"]],
			"res_id"   : sfs_id.id,
			"target"   : "new",
		}

	@api.model
	def create(self,vals):
		t = super(hr_five_category_lines,self).create(vals)

		hlc_basico     = self.env['hr.lista.conceptos'].search([('code','=','001')])
		hlc_a_familiar = self.env['hr.lista.conceptos'].search([('code','=','002')])
		hp_a_familiar  = self.env['hr.parameters'].search([('num_tipo','=',10001)])

		vals_lines = {
			'five_line_id': t.id,
			'concepto_id' : hlc_basico[0].id if hlc_basico[0].id else False,
			'january'     : t.employee_id.basica,
			'february'    : t.employee_id.basica,
			'march'       : t.employee_id.basica,
			'april'       : t.employee_id.basica,
			'may'         : t.employee_id.basica,
			'june'        : t.employee_id.basica,
			'july'        : t.employee_id.basica,
			'august'      : t.employee_id.basica,
			'september'   : t.employee_id.basica,
			'october'     : t.employee_id.basica,
			'november'    : t.employee_id.basica,
			'december'    : t.employee_id.basica,
		}
		hfcp = self.env['hr.five.category.proy'].create(vals_lines)

		af = 0
		if t.employee_id.children_number > 0:
			af = hp_a_familiar[0].monto if len(hp_a_familiar) > 0 else 0
		vals_lines = {
			'five_line_id': t.id,
			'concepto_id' : hlc_a_familiar[0].id if hlc_a_familiar[0].id else False,
			'january'     : af,
			'february'    : af,
			'march'       : af,
			'april'       : af,
			'may'         : af,
			'june'        : af,
			'july'        : af,
			'august'      : af,
			'september'   : af,
			'october'     : af,
			'november'    : af,
			'december'    : af,
		}
		hfcp = self.env['hr.five.category.proy'].create(vals_lines)

		hcrl = self.env['hr.concepto.remunerativo.line'].search([('incoming_type','=','ordinary')])
		for con in hcrl:
			hfcp = self.env['hr.five.category.proy'].create({'five_line_id':t.id, 'concepto_id': con.concepto.id})

		hcrl = self.env['hr.concepto.remunerativo.line'].search([('incoming_type','=','extraordinary')])
		for con in hcrl:
			hfcp = self.env['hr.five.category.concepts'].create({'five_line_id':t.id, 'concepto_id': con.concepto.id})
			if hfcp.concepto_id.code == '001':
				hfcp.january  = t.employee_id.basica if t.employee_id.no_domiciliado else 0
				hfcp.february  = t.employee_id.basica
				hfcp.march     = t.employee_id.basica
				hfcp.april     = t.employee_id.basica
				hfcp.may       = t.employee_id.basica
				hfcp.june      = t.employee_id.basica
				hfcp.july      = t.employee_id.basica
				hfcp.august    = t.employee_id.basica
				hfcp.september = t.employee_id.basica
				hfcp.october   = t.employee_id.basica
				hfcp.november  = t.employee_id.basica
				hfcp.december  = t.employee_id.basica				
			if hfcp.concepto_id.code == '002':
				hfcp.january   = af if t.employee_id.no_domiciliado else 0
				hfcp.february  = af
				hfcp.march     = af
				hfcp.april     = af
				hfcp.may       = af
				hfcp.june      = af
				hfcp.july      = af
				hfcp.august    = af
				hfcp.september = af
				hfcp.october   = af
				hfcp.november  = af
				hfcp.december  = af
		
		vals_lines = {
			'five_line_id': t.id,

			'row_text' : 'Grati. Jul. y Dic.',
			'january'  : 0,
			'february' : 0,
			'march'    : 0,
			'april'    : 0,
			'may'      : 0,
			'june'     : 0,
			'july'     : 0,
			'august'   : 0,
			'september': 0,
			'october'  : 0,
			'november' : 0,
			'december' : 0,
		}
		hfcp = self.env['hr.five.category.jul.dic'].create(vals_lines)
		return t

class hr_five_category_proy(models.Model):
	_name = 'hr.five.category.proy'
	
	five_line_id = fields.Many2one('hr.five.category.lines','Main')

	concepto_id = fields.Many2one('hr.lista.conceptos','Concepto')
	january     = fields.Float('Enero',digist=(12,2))
	february    = fields.Float('Febrero',digist=(12,2))
	march       = fields.Float('Marzo',digist=(12,2))
	april       = fields.Float('Abril',digist=(12,2))
	may         = fields.Float('Mayo',digist=(12,2))
	june        = fields.Float('Junio',digist=(12,2))
	july        = fields.Float('Julio',digist=(12,2))
	august      = fields.Float('Agosto',digist=(12,2))
	september   = fields.Float('Setiembre',digist=(12,2))
	october     = fields.Float('Octubre',digist=(12,2))
	november    = fields.Float('Noviembre',digist=(12,2))
	december    = fields.Float('Diciembre',digist=(12,2))


class hr_five_category_concepts(models.Model):
	_name = 'hr.five.category.concepts'
	
	five_line_id = fields.Many2one('hr.five.category.lines','Main')

	concepto_id = fields.Many2one('hr.lista.conceptos','Concepto')
	january     = fields.Float('Enero',digist=(12,2))
	february    = fields.Float('Febrero',digist=(12,2))
	march       = fields.Float('Marzo',digist=(12,2))
	april       = fields.Float('Abril',digist=(12,2))
	may         = fields.Float('Mayo',digist=(12,2))
	june        = fields.Float('Junio',digist=(12,2))
	july        = fields.Float('Julio',digist=(12,2))
	august      = fields.Float('Agosto',digist=(12,2))
	september   = fields.Float('Setiembre',digist=(12,2))
	october     = fields.Float('Octubre',digist=(12,2))
	november    = fields.Float('Noviembre',digist=(12,2))
	december    = fields.Float('Diciembre',digist=(12,2))

class hr_five_category_jul_dic(models.Model):
	_name = 'hr.five.category.jul.dic'
	
	five_line_id = fields.Many2one('hr.five.category.lines','Main')

	row_text = fields.Char(u'5ta Categoría')
	january   = fields.Float('Enero',digist=(12,2))
	february  = fields.Float('Febrero',digist=(12,2))
	march     = fields.Float('Marzo',digist=(12,2))
	april     = fields.Float('Abril',digist=(12,2))
	may       = fields.Float('Mayo',digist=(12,2))
	june      = fields.Float('Junio',digist=(12,2))
	july      = fields.Float('Julio',digist=(12,2))
	august    = fields.Float('Agosto',digist=(12,2))
	september = fields.Float('Setiembre',digist=(12,2))
	october   = fields.Float('Octubre',digist=(12,2))
	november  = fields.Float('Noviembre',digist=(12,2))
	december  = fields.Float('Diciembre',digist=(12,2))

##############################################################
# ESTA TABLA SOLAMENTE ES UTILIZADAD PARA MOSTRAR INFORMACION
# DE LOS CALCULOS HECHOS EN LA FUNCION "PROCESAR"
##############################################################
class hr_five_category_calculo(models.Model):
	_name = 'hr.five.category.calculo'
	
	five_line_id = fields.Many2one('hr.five.category.lines','Main')

	is_red = fields.Boolean('Linea Roja', default=False)

	row_text  = fields.Char(u'5ta categoría')
	january   = fields.Float('Enero',digist=(12,2))
	february  = fields.Float('Febrero',digist=(12,2))
	march     = fields.Float('Marzo',digist=(12,2))
	april     = fields.Float('Abril',digist=(12,2))
	may       = fields.Float('Mayo',digist=(12,2))
	june      = fields.Float('Junio',digist=(12,2))
	july      = fields.Float('Julio',digist=(12,2))
	august    = fields.Float('Agosto',digist=(12,2))
	september = fields.Float('Setiembre',digist=(12,2))
	october   = fields.Float('Octubre',digist=(12,2))
	november  = fields.Float('Noviembre',digist=(12,2))
	december  = fields.Float('Diciembre',digist=(12,2))