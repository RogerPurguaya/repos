# -*- coding: utf-8 -*-

from odoo import fields, models,api,exceptions, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
import base64,os

class glass_pdf_file(models.Model):
	_name='glass.pdf.file'

	pdf_file = fields.Binary('Croquis')
	pdf_name = fields.Char('Archivo')
	file_name = fields.Char('Archivo')
	is_used = fields.Boolean('Usado',default=False)
	op_id = fields.Many2one('glass.order',u'Orden de Producción')
	sale_id = fields.Many2one('sale.order','Pedido de venta',required=True,ondelete='cascade')
	is_editable = fields.Boolean('Editable',default=True)
	path_pdf = fields.Char(string='Ruta del Pdf')
	_rec_name="pdf_name"

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.op_id:
				raise UserError('No es posible eliminar\nLa Orden de producción %s utiliza este archivo.'%rec.op_id.name)
			if rec.path_pdf and os.path.exists(rec.path_pdf):
				os.remove(rec.path_pdf)
			else:
				print('Path file does not exist !')	
		return super(glass_pdf_file,self).unlink()

	@api.one
	def save_pdf(self):
		self.editable_croquis=False
		return True

	@api.multi
	def show_sketch(self):
		vals = {}
		wizard = self.env['add.sketch.file'].sudo()
		try:
			with open(self.path_pdf,"rb") as pdf_file:
				vals = {'sketch': pdf_file.read().encode("base64")}
		except TypeError as e:
			print(u'Path does not exist!')
			vals = {'message': 'Archivo Croquis removido o no encontrado!',}
		except IOError as e:
			print(u'Pdf file not found or not available!')
			vals = {'message': 'Archivo Croquis removido o no encontrado!',}
		wizard = wizard.create(vals)
		module = __name__.split('addons.')[1].split('.')[0]
		return {
			'name':'Ver Croquis',
			'res_id':wizard.id,
			'type': 'ir.actions.act_window',
			'res_model': wizard._name,
			'view_id':self.env.ref('%s.only_view_sketch_file_view_form'%module).id,
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	op_count = fields.Integer(u'Ordenes de producción',compute="getops",copy=False)
	op_control = fields.Char('Control de OP',compute='_get_state_op')
	op_ids = fields.One2many('glass.order',string=u'Ordenes de producción',compute="getops",copy=False)
	op_returned_ids = fields.One2many('glass.order',string=u'OP devueltas',compute="get_returned_ops",copy=False)
	op_returned_count = fields.Integer(u'Nro OP devueltas',compute="get_returned_ops",copy=False)
	files_ids = fields.One2many('glass.pdf.file','sale_id','Croquis',copy=False)
	reference_order = fields.Char(string='Referencia OP',copy=False,track_visibility='onchange')
	count_files = fields.Integer('Files',compute='_get_count_files')
	type_sale = fields.Selection([('distribution',u'Distribución'),('production',u'Producción'),('services','Servicios')])

	@api.depends('files_ids')
	def _get_count_files(self):
		for rec in self:
			rec.count_files = len(rec.files_ids)

	@api.multi
	def add_sketch_file(self):
		module = __name__.split('addons.')[1].split('.')[0]
		return {
			'name':'Agregar Archivo Croquis',
			'view_id': self.env.ref('%s.add_sketch_file_view_form'%module).id,
			'type': 'ir.actions.act_window',
			'res_model': 'add.sketch.file',
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
			'context':{'sale_order_id':self.id}
		}

	@api.model
	def create(self, values):
		t = super(SaleOrder, self).create(values)
		type_sale = values.get('type_sale',False)
		if type_sale == 'production':
			seq = self.env['ir.sequence'].search([('code','=','sale.order')])
			prod_seq = self.env['glass.order.config'].search([],limit=1).seq_sale_prod
			if not prod_seq:
				raise UserError(u'No ha configurado la secuencia para ventas de producción')
			t.name = prod_seq.next_by_id()
			seq.write({'number_next_actual':seq.number_next_actual-seq.number_increment})
		return t
	
	#@api.one
	@api.depends('op_ids','order_line')
	def _get_state_op(self):
		for order in self:
			ops = order.op_ids
			services = order.order_line.filtered(lambda x: x.product_id.type=='service')
			calculators = order.order_line.mapped('calculator_id')
			if calculators and len(services) != len(order.order_line):
				prod = calculators.filtered(lambda x: x.qty_invoiced_rest==0)
				if len(prod)==len(calculators) and ops: # todo producido
					order.op_control = 'OP GENERADA'
				else:
					order.op_control = 'OP PARCIAL' if ops else 'OP PENDIENTE'
			else:
				order.op_control = 'NO APLICA' # si no tiene calculadora y todas las lineas son servicios

	@api.depends('order_line.calculator_id')
	def getops(self):
		ops = self.env['glass.order']
		for order in self:
			for calc in order.order_line.mapped('calculator_id'):
				ops |= calc._get_glass_order_ids()
			order.op_count = len(ops)
			order.op_ids = ops.ids

	@api.one
	def get_returned_ops(self):
		# obtenemos de la siguiente forma xq cuando se retorna una op, se borra el vínculo de la op con la línea de calculadora que la generó.
		ops = self.env['glass.order'].search([('sale_order_id','=',self.id),('state','=','returned')])
		self.op_returned_count=len(ops)
		self.op_returned_ids=ops.ids

	def loadproductionwizard(self):
		self.ensure_one()
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.build_glass_order_wizard_form_view' % module)
		wizard = self.env['build.glass.order.wizard'].sudo().create({'sale_id':self.id})
		available_files = self.files_ids.filtered(lambda x: not x.is_used and x.is_editable)
		return {
			'name':u'Generar Órden de Producción',
			'res_id':wizard.id,
			'view_type':'form',
			'view_mode':'form',
			'view_id': view.id,
			'res_model':wizard._name,
			'type':'ir.actions.act_window',
			'target': 'new',
			'context':{'file_domain':[('id','in',available_files.ids)]}
		}

	@api.multi
	def show_po_list(self):
		self.ensure_one()
		if len(self.op_ids)==1:
			return {
				'name':u'Órdenes de producción',
				'res_id':self.op_ids[0].id,
				'view_type':'form',
				'view_mode':'form',
				'res_model':'glass.order',
				'type':'ir.actions.act_window',
			}
		elif len(self.op_ids)>1:
			return {
				'name':u'Órdenes de producción',
				'view_type':'form',
				'view_mode':'tree,form',
				'res_model':'glass.order',
				'type':'ir.actions.act_window',
				'domain':[('id','in',self.op_ids.ids)]
			}
		return True	
	
	@api.multi
	def show_po_returned_list(self):
		self.ensure_one()
		if len(self.op_returned_ids)==1:
			return {
				'name':u'Órdenes de producción Devueltas',
				'res_id':self.op_returned_ids[0].id,
				'view_type':'form',
				'view_mode':'form',
				'res_model':'glass.order',
				'type':'ir.actions.act_window',
			}
		elif len(self.op_returned_ids)>1:
			return {
				'name':u'Órdenes de producción Devueltas',
				'view_type':'form',
				'view_mode':'tree,form',
				'res_model':'glass.order',
				'type':'ir.actions.act_window',
				'domain':[('id','in',self.op_returned_ids.ids)]
			}
		return True	

	# @api.multi
	# def end_state_order(self):
	# 	self.op_control = 'OP GENERADA'
	# 	return True

	@api.one
	def unlink(self):
		for sale in self:
			if sale.op_count>0:
				raise UserError(u"No se puede eliminar un pedido de venta si generó Órdenes de Producción")
		return super(SaleOrder,self).unlink()

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'
	
	def get_glass_order_lines(self):
		self.ensure_one()
		return self.calculator_id._get_glass_order_ids().mapped('line_ids')

	@api.multi
	def unlink(self):
		for line in self:
			if line.order_id.state in ('sale','done'):
				raise UserError(u'No es posible eliminar una línea si el estado de su pedido es distinto a borrador')
			if line.calculator_id._get_glass_order_ids():
				raise UserError(u'No es posible eliminar la línea de pedido cuando su calculadora tiene Órdenes de Producción')
			line.calculator_id.unlink()
		return super(SaleOrderLine,self).unlink()