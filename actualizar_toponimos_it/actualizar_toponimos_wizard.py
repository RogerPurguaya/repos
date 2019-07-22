# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import Warning
import time
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from suds.client import Client
from openerp.osv import osv
import re
import base64
from odoo import models, fields, api
import codecs
values = {}

import datetime



class actualizar_toponimos_wizard(models.TransientModel):
	_name = 'actualizar.toponimos.wizard'
	select = fields.Selection(
		[('dni', 'DNI'), ('ruc', 'RUC')],
		string='Tipo de Documento',
		default='ruc', required=True)

	@api.multi
	def actualizar_toponimos(self):
		if self.select == 'ruc':
			t = self.env['res.partner'].search([('type_document_partner_it.name','=','RUC')])
			for i in t:
				if not i.parent_id and i.nro_documento and (i.type == 'contact' or not i.type):
					i.verify_ruc()
		else:
			t = self.env['res.partner'].search([('type_document_partner_it.name','=','DNI')])
			for i in t:
				if not i.parent_id and i.nro_documento and (i.type == 'contact' or not i.type):
					i.verify_dni()

class res_partner(models.Model):
	_inherit = 'res.partner'

	@api.one
	def verify_ruc(self):
		client = Client("http://ws.insite.pe/sunat/ruc.php?wsdl",faults=False,cachingpolicy= 1, location= "http://ws.insite.pe/sunat/ruc.php?wsdl")
		result = client.service.consultaRUC(self.nro_documento,"jtejada@itgrupo.net","ZDI-9DJ-YA8-D8C","plain")
		texto = result[1].split('|')
		flag = False
		for i in texto:
			tmp = i.split('=')
			if tmp[0] == 'status_msg' and tmp[1] == 'OK/1':
				flag = True

		print texto
		if flag:
			for j in texto:
				tmp = j.split('=')
				if tmp[0] == 'n1_alias':
					self.name = tmp[1]
				if tmp[0] == 'n1_direccion':
					self.street = tmp[1]
				if tmp[0] == 'n1_ubigeo':
					ubigeo=self.env['res.country.state'].search([('code','=',tmp[1])])
					if ubigeo:
						self.zip = tmp[1]
						pais =self.env['res.country'].search([('code','=','PE')]) 
						ubidepa=tmp[1][0:2]
						ubiprov=tmp[1][0:4]
						ubidist=tmp[1][0:6]

						departamento = self.env['res.country.state'].search([('code','=',ubidepa),('country_id','=',pais.id)])
						provincia  = self.env['res.country.state'].search([('code','=',ubiprov),('country_id','=',pais.id)])
						distrito = self.env['res.country.state'].search([('code','=',ubidist),('country_id','=',pais.id)])

						self.country_id=pais.id
						self.state_id=departamento.id
						self.province_id = provincia.id
						self.district_id = distrito.id
				if tmp[0] == 'n1_estado':
					self.ruc_state = tmp[1]
				if tmp[0] == 'n1_condicion':
					self.ruc_condition = tmp[1]
				
		else:
			print("no")	

	@api.multi
	def verify_dni(self):
		if self.nro_documento == False:
			raise osv.except_osv('Alerta!',"Debe seleccionar un DNI")
		client = Client("http://reniec.insite.pe/soap?wsdl",faults=False,cachingpolicy= 1, location= "http://reniec.insite.pe/index.php/soap?wsdl")
		print("DNI",str(self.nro_documento))
		try: 
			result = client.service.consultar(str(self.nro_documento),"jtejada@itgrupo.net","ZDI-9DJ-YA8-D8C","plain")
			print('result',result)
			texto = result[1].split('|')
			flag = False
			nombres = ''
			a_paterno = ''
			a_materno = ''
			for c in texto:
				tmp = c.split('=')
				if tmp[0] == 'status_id' and tmp[1] == '102':
					raise osv.except_osv('Alerta!','El DNI debe tener al menos 8 digitos de longitud')
				if tmp[0] == 'status_id' and tmp[1] == '103':
					raise osv.except_osv('Alerta!','El DNI debe ser un valor numerico')
				if tmp[0] == 'reniec_nombres' and tmp[1] != '':
					nombres = tmp[1]
					self.nombre = tmp[1]
				if tmp[0] == 'reniec_paterno' and tmp[1] != '':
					a_paterno = tmp[1]
					self.apellido_p = tmp[1]
				if tmp[0] == 'reniec_materno' and tmp[1] != '':
					a_materno = tmp[1]
					self.apellido_m = tmp[1]
			self.name = (nombres + " " + a_paterno + " " + a_materno).strip()
		except Exception as e:
			print("no")
		
