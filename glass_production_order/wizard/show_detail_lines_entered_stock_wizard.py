from odoo import fields,models,api,exceptions, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta
from functools import reduce

# Wizard contenedor para ver los cristales de los stock_moves a retornar:
class Detail_Crystals_Entered_Wizard(models.TransientModel):
	_name = 'detail.crystals.entered.wizard'
	detail_lines = fields.One2many('detail.crystals.entered.wizard.line','wizard_id')
	warning_message = fields.Char()

	@api.multi
	def select_crystals_to_return(self):
		selected_lines = self.detail_lines.filtered(lambda i: i.check)
		if len(selected_lines) == 0:
			raise exceptions.Warning('Debe seleccionar un(os) cristal(es) para devolver.')
		msg = ''
		sended = selected_lines.filtered(lambda x: x.entregado)
		breaks = selected_lines.filtered(lambda x: x.is_break)
		not_motive = selected_lines.filtered(lambda x: not x.motive)
		packing_list = selected_lines.filtered(lambda x: x.packing_list)
		for item in sended:
			msg+='->'+item.order_id.name+' '+str(item.crystal_num)+': Entregado'+'\n'
		for item in breaks:
			msg+='->'+item.order_id.name+' '+str(item.crystal_num)+': Roto'+'\n'
		for item in not_motive:
			msg+='->'+item.order_id.name+' '+str(item.crystal_num)+': Sin Motivo'+'\n'
		for item in packing_list:
			msg+='->'+item.order_id.name+' '+str(item.crystal_num)+': En Packing List'+'\n'
		if msg != '':
			raise exceptions.Warning('No es posible devolver los siguientes cristales:\n' + msg)

		src_picking = selected_lines.mapped('picking_id')[0]
		try:
			config = self.env['glass.order.config'].search([])[0]
		except IndexError as e:
			raise UserError(u'No se encontraron los valores de configuracion de produccion')		
		type_return = config.picking_type_return_pt
		if not type_return:
			raise UserError(u'No existe el tipo de Picking de retorno en la configuracion de Produccion')

		return_picking = self.env['stock.picking'].create({
				'picking_type_id':type_return.id,
				'partner_id': None,
				'date': (datetime.now()-timedelta(hours=5)).date(),
				'fecha_kardex': datetime.now().date(),
				'origin': src_picking.name,
				'location_dest_id': type_return.default_location_dest_id.id,
				'location_id': type_return.default_location_src_id.id,
				'company_id': self.env.user.company_id.id,
				'einvoice_12': config.traslate_motive_return_pt.id,
			})

		for product in set(selected_lines.mapped('product_id')):
			fil_list = selected_lines.filtered(lambda x:x.product_id.id == product.id)
			total_area = reduce(lambda x,y:x+y,fil_list.mapped('area'))
			move = self.env['stock.move'].create({
				'name': product.name or '',
				'product_id': product.id,
				'product_uom': product.uom_id.id,
				'date': (datetime.now()-timedelta(hours=5)).date(),
				'date_expected': (datetime.now()-timedelta(hours=5)).date(),
				'location_id': type_return.default_location_src_id.id,
				'location_dest_id': type_return.default_location_dest_id.id,
				'picking_id': return_picking.id,
				'state': 'draft',
				'company_id': self.env.user.company_id.id,
				'picking_type_id': type_return.id,
				'origin': src_picking.name,
				'route_ids': type_return.warehouse_id and [(6, 0, [x.id for x in type_return.warehouse_id.route_ids])] or [],
				'warehouse_id': type_return.warehouse_id.id,
				'product_uom_qty': total_area,
				'glass_order_line_ids': [(6,0,fil_list.mapped('glass_line_id').ids)]
			})

			try:
				return_picking.action_confirm()
				return_picking.force_assign() # forzar disponibilidad
			except UserError as e:
				raise UserError('No fue posible forzar la disponibilidad:\nPosible Causa:\n'+str(e))
			context = None
			action = return_picking.do_new_transfer()
			if type(action) == type({}):
				if action['res_model'] == 'stock.immediate.transfer':
					context = action['context']
					sit = self.env['stock.immediate.transfer'].with_context(context).create({'pick_id':return_picking.id})	
					try:
						sit.process()
					except UserError as e:
						raise UserError(u'No se ha podido realizar la devolucion.\nMotivo:'+str(e))
				if action['res_model'] == 'confirm.date.picking':
					context = action['context']
					cdp = self.env['confirm.date.picking'].with_context(context).create({'pick_id':return_picking.id,'date':return_picking.fecha_kardex})
					res = cdp.changed_date_pincking()
			
			for line in selected_lines:
				line.lot_line_id.is_break=True
				stage_obj = self.env['glass.stage.record'].create({
					'user_id':self.env.uid,
					'date':(datetime.now()-timedelta(hours=5)).date(),
					'time':(datetime.now()-timedelta(hours=5)).time(),
					'stage':'roto',
					'lot_line_id':line.lot_line_id.id,
					'break_motive':line.motive,
					'break_stage':'ingresado',
				})
				line.glass_line_id.write({
					'last_lot_line':line.lot_line_id.id,
					'glass_break':True,
					'lot_line_id':False,
					'is_used':False,
					'state':'process',
		 		})

		return {
				'res_id': return_picking.id,
				'type': 'ir.actions.act_window',
				'res_model': 'stock.picking',
				'view_mode': 'form',
				'view_type': 'form',
				}

 # Contenedor para lineas de cristles a devolver desde APT
class Detail_Crystals_Entered_Wizard_Lines(models.TransientModel):
	_name = 'detail.crystals.entered.wizard.line'
	
	check = fields.Boolean(string='Seleccion')
	wizard_id = fields.Many2one('detail.crystals.entered.wizard')
	move_id = fields.Many2one('stock.move')
	glass_line_id = fields.Many2one('glass.order.line')
	lot_line_id = fields.Many2one('glass.lot.line')
	order_id = fields.Many2one(related='glass_line_id.order_id')
	lot_id  = fields.Many2one(related='lot_line_id.lot_id',string='Lote')
	base1   = fields.Integer(related='glass_line_id.base1',string='Base 1')
	base2   = fields.Integer(related='glass_line_id.base2',string='Base 2')
	height1 = fields.Integer(related='glass_line_id.altura1',string='Altura 1')
	height2 = fields.Integer(related='glass_line_id.altura2',string='Altura 2')
	crystal_num =  fields.Char(related='glass_line_id.crystal_number',string='Num. Cristal')
	quantity    = fields.Float(related='move_id.product_qty') 
	picking_id  = fields.Many2one(related='move_id.picking_id') 
	product_id = fields.Many2one(related='glass_line_id.product_id',string='Producto')
	area = fields.Float(related='glass_line_id.area',string='Area')
	templado  = fields.Boolean(related='lot_line_id.templado',string='Templado')
	ingresado = fields.Boolean(related='lot_line_id.ingresado',string='Ingresado')
	entregado = fields.Boolean(related='lot_line_id.entregado',string='Entregado')
	packing_list = fields.Boolean(related='glass_line_id.in_packing_list',string='Packing List')
	req_id = fields.Many2one(related='lot_line_id.lot_id.requisition_id',string='Requisicion')
	is_break = fields.Boolean(related='lot_line_id.is_break')
	#campo para motivo de rotura:
	motive = fields.Selection([
		('Vidrio roto','Vidrio roto'), 
		('Error entalle','Error entalle'), 
		('Error medidas','Error medidas'), 
		('Vidrio rayado','Vidrio rayado'), 
		('Planimetria','Planimetria'), 
		('Error ventas','Error ventas'), 
		('Materia prima','Materia prima')])
