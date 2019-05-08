# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from openerp.osv import osv
import base64
from zipfile import ZipFile


class costo_produccion_it(models.Model):
	_name = 'costo.produccion.it'

	periodo = fields.Many2one('account.period','Periodo')
	fecha  = fields.Date('Fecha de Asiento')

	@api.multi
	def do_rebuild(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		file_path = direccion + 'categorias_sin_cuenta.txt'

		t = "'{"
		for i in self.env['product.product'].search([]):
			t += str(i.id) + ','

		t=t[:-1] + "}'"

		fecha_inianio = str(self.periodo.date_start).replace('-','')
		fechafin = str(self.periodo.date_stop).replace('-','')

		m = "'{"
		origen = [0,0,0]
		for i in self.env['stock.location'].search([]):
			if i.usage == 'internal':
				origen.append(i.id)
				m += str(i.id) + ','

				
		destino = [0,0,0]
		for i in self.env['stock.location'].search([]):
			if i.usage == 'production':
				destino.append(i.id)
				m += str(i.id) + ','
		m=m[:-1] + "}'"

		self.env.cr.execute("""
			select aa.id,sum(credit) as credit from get_kardex_v("""+fecha_inianio+""","""+fechafin+""",""" + t + """::INT[],""" + m + """::INT[]) as X
			inner join account_analytic_account aaa on aaa.name = X.ctanalitica
			inner join centro_costo cc on cc.id = aaa.cost_center_id
			inner join product_product pp on pp.id = X.product_id
			inner join product_template pt on pt.id = pp.product_tmpl_id
			inner join account_account aa on aa.id = (
				CASE WHEN  cc.columna == '1' THEN pt.extraccion_acc ELSE				
					CASE WHEN  cc.columna == '2' THEN pt.trituracion_acc ELSE
						CASE WHEN  cc.columna == '3' THEN pt.calcinacion_acc ELSE
							CASE WHEN  cc.columna == '4' THEN pt.micronizado_acc ELSE
								CASE WHEN  cc.columna == '5' THEN pt.administracion_acc ELSE
									CASE WHEN  cc.columna == '6' THEN pt.ventas_acc ELSE				
										CASE WHEN  cc.columna == '7' THEN pt.capacitacion_acc ELSE				
											CASE WHEN  cc.columna == '8' THEN pt.promocion_acc ELSE				
												CASE WHEN  cc.columna == '9' THEN pt.gastos_acc ELSE	0													
												END
											END
										END
									END
								END
							END
						END
					END
				END
			)
			where (ubicacion_origen in """ + str(tuple(origen)) + """ and ubicacion_destino in """ + str(tuple(destino)) + """)
			and fecha >= '"""+str(self.periodo.date_start)+"""' and fecha <= '"""+str(self.periodo.date_stop)+"""'
			and aaa.account_account_moorage_credit_id is not null
			group by aa.id

			--select aaa.account_account_moorage_id, sum(credit) as credit from get_kardex_v("""+fecha_inianio+""","""+fechafin+""",""" + t + """::INT[],""" + m + """::INT[]) as X
			--left join account_analytic_account aaa on aaa.name = X.ctanalitica
--
--			where (ubicacion_origen in """ + str(tuple(origen)) + """ and ubicacion_destino in """ + str(tuple(destino)) + """)
--			and fecha >= '"""+str(self.periodo.date_start)+"""' and fecha <= '"""+str(self.periodo.date_stop)+"""'
--			and aaa.account_account_moorage_id is not null and aaa.account_account_moorage_credit_id is not null
--			group by aaa.account_account_moorage_id
			   """)
		
		linea_debe = []

		for i in self.env.cr.fetchall():
			if i[0]:
				linea_debe.append( (i[0],i[1]) )


		self.env.cr.execute("""
			select aaa.account_account_moorage_credit_id, sum(credit) as credit from get_kardex_v("""+fecha_inianio+""","""+fechafin+""",""" + t + """::INT[],""" + m + """::INT[]) as X
			left join account_analytic_account aaa on aaa.name = X.ctanalitica

			where (ubicacion_origen in """ + str(tuple(origen)) + """ and ubicacion_destino in """ + str(tuple(destino)) + """)
			and fecha >= '"""+str(self.periodo.date_start)+"""' and fecha <= '"""+str(self.periodo.date_stop)+"""'
			and aaa.account_account_moorage_id is not null and aaa.account_account_moorage_credit_id is not null
			group by aaa.account_account_moorage_credit_id
			   """)

		linea_haber = []

		for i in self.env.cr.fetchall():
			if i[0]:
				linea_haber.append( (i[0],i[1]) )


		parametros = self.env['main.parameter'].search([])[0]

		valsC = {
			'period_id':self.periodo.id,
			'journal_id':parametros.diario_destino.id,
			'ref':'CP-'+ self.periodo.code.replace('/','-'),
			'date':self.fecha,
		}
		asiento = self.env['account.move'].create(valsC)

		for i in linea_debe:
			dataL = {
				'name':'ASIENTO DE COSTO DE PRODUCCION '+ self.periodo.code.replace('/','-'),
				'account_id':i[0],
				'nro_comprobante':'CP-'+ self.periodo.code.replace('/','-'),
				'debit': i[1] ,
				'credit': 0,
				'move_id': asiento.id,
			}
			self.env['account.move.line'].create(dataL)

		for i in linea_haber:
			dataL = {
				'name':'ASIENTO DE COSTO DE PRODUCCION '+ self.periodo.code.replace('/','-'),
				'account_id':i[0],
				'nro_comprobante':'CP-'+ self.periodo.code.replace('/','-'),
				'debit': 0,
				'credit': i[1],
				'move_id': asiento.id,
			}
			self.env['account.move.line'].create(dataL)




		fo = open(file_path, "w")
		fo.write('Cuenta Analitica' + "\r\n");
		fo.write('----------------------------------' + "\r\n");

		self.env.cr.execute("""
			select distinct X.ctanalitica from get_kardex_v("""+fecha_inianio+""","""+fechafin+""",""" + t + """::INT[],""" + m + """::INT[]) as X
			left join account_analytic_account aaa on aaa.name = X.ctanalitica

			where (ubicacion_origen in """ + str(tuple(origen)) + """ and ubicacion_destino in """ + str(tuple(destino)) + """)
			and fecha >= '"""+str(self.periodo.date_start)+"""' and fecha <= '"""+str(self.periodo.date_stop)+"""'
			and ( aaa.account_account_moorage_credit_id is  null )
			   """)

		for i in self.env.cr.fetchall():
			if i[0]:
				fo.write('-- '+i[0].upper() + "\r\n");


		self.env.cr.execute("""
			select pp.name_template,aaa.name,cc.name,aa.code from get_kardex_v("""+fecha_inianio+""","""+fechafin+""",""" + t + """::INT[],""" + m + """::INT[]) as X
			inner join account_analytic_account aaa on aaa.name = X.ctanalitica
			left join centro_costo cc on cc.id = aaa.cost_center_id
			inner join product_product pp on pp.id = X.product_id
			inner join product_template pt on pt.id = pp.product_tmpl_id
			left join account_account aa on aa.id = (
				CASE WHEN  cc.columna == '1' THEN pt.extraccion_acc ELSE				
					CASE WHEN  cc.columna == '2' THEN pt.trituracion_acc ELSE
						CASE WHEN  cc.columna == '3' THEN pt.calcinacion_acc ELSE
							CASE WHEN  cc.columna == '4' THEN pt.micronizado_acc ELSE
								CASE WHEN  cc.columna == '5' THEN pt.administracion_acc ELSE
									CASE WHEN  cc.columna == '6' THEN pt.ventas_acc ELSE				
										CASE WHEN  cc.columna == '7' THEN pt.capacitacion_acc ELSE				
											CASE WHEN  cc.columna == '8' THEN pt.promocion_acc ELSE				
												CASE WHEN  cc.columna == '9' THEN pt.gastos_acc ELSE	0													
												END
											END
										END
									END
								END
							END
						END
					END
				END
			)
			where (ubicacion_origen in """ + str(tuple(origen)) + """ and ubicacion_destino in """ + str(tuple(destino)) + """)
			and fecha >= '"""+str(self.periodo.date_start)+"""' and fecha <= '"""+str(self.periodo.date_stop)+"""'
			and aaa.account_account_moorage_credit_id is not null and (cc.name is null or aa.code is null)
			 """ )


		for i in self.env.cr.fetchall():
			if i[0]:
				fo.write('-- '+i[0].upper() +'-- '+i[1].upper() +'-- '+i[2].upper() +'-- '+i[3].upper() + "\r\n");

		fo.close()
		f = open(file_path, 'r')
		vals = {
			'output_name': 'analitica_sin_cuenta.txt',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    'view_mode': 'form',
		    "view_type": "form",
		    "res_id": sfs_id.id,
		    "target": "new",
		}