odoo.define('cashbox.popups', function (require) {
"use strict";

// This file contains the Popups.
// Popups must be loaded and named in chrome.js. 
// They are instanciated / destroyed with the .gui.show_popup()
// and .gui.close_popup() methods.

var PosBaseWidget = require('cashbox.BaseWidget');
var gui = require('cashbox.gui');
var _t  = require('web.core')._t;
var utils = require('web.utils');
var round_di = utils.round_decimals;
var models = require('cashbox.models');


var PopupWidget = PosBaseWidget.extend({
    template: 'PopupWidget',
    init: function(parent, args) {
        this._super(parent, args);
        this.options = {};
    },
    events: {
        'click .button.cancel':  'click_cancel',
        'click .button.confirm': 'click_confirm',
        'click .selection-item': 'click_item',
        'click .input-button':   'click_numpad',
        'click .mode-button':    'click_numpad',
    },

    // show the popup !  
    show: function(options){
        if(this.$el){
            this.$el.removeClass('oe_hidden');
        }
        
        if (typeof options === 'string') {
            this.options = {title: options};
        } else {
            this.options = options || {};
        }

        this.renderElement();

        // popups block the barcode reader ... 
        if (this.pos.barcode_reader) {
            this.pos.barcode_reader.save_callbacks();
            this.pos.barcode_reader.reset_action_callbacks();
        }
    },

    // called before hide, when a popup is closed.
    // extend this if you want a custom action when the 
    // popup is closed.
    close: function(){
        if (this.pos.barcode_reader) {
            this.pos.barcode_reader.restore_callbacks();
        }
    },

    // hides the popup. keep in mind that this is called in 
    // the initialization pass of the pos instantiation, 
    // so you don't want to do anything fancy in here
    hide: function(){
        if (this.$el) {
            this.$el.addClass('oe_hidden');
        }
    },

    // what happens when we click cancel
    // ( it should close the popup and do nothing )
    click_cancel: function(){
        this.gui.close_popup();
        if (this.options.cancel) {
            this.options.cancel.call(this);
        }
    },

    // what happens when we confirm the action
    click_confirm: function(){
        this.gui.close_popup();
        if (this.options.confirm) {
            this.options.confirm.call(this);
        }
    },

    // Since Widget does not support extending the events declaration
    // we declared them all in the top class.
    click_item: function(){},
    click_numad: function(){},
});
gui.define_popup({name:'alert', widget: PopupWidget});

var ErrorPopupWidget = PopupWidget.extend({
    template:'ErrorPopupWidget',
    show: function(options){
        this._super(options);
        this.gui.play_sound('error');
    },
});
gui.define_popup({name:'error', widget: ErrorPopupWidget});


var ErrorTracebackPopupWidget = ErrorPopupWidget.extend({
    template:'ErrorTracebackPopupWidget',
    show: function(opts) {
        var self = this;
        this._super(opts);

        this.$('.download').off('click').click(function(){
            self.gui.prepare_download_link(self.options.body,
                _t('error') + ' ' + moment().format('YYYY-MM-DD-HH-mm-ss') + '.txt',
                '.download', '.download_error_file');
        });

        this.$('.email').off('click').click(function(){
            self.gui.send_email( self.pos.company.email,
                _t('IMPORTANT: Bug Report From Odoo Point Of Sale'),
                self.options.body);
        });
    }
});
gui.define_popup({name:'error-traceback', widget: ErrorTracebackPopupWidget});


var ErrorBarcodePopupWidget = ErrorPopupWidget.extend({
    template:'ErrorBarcodePopupWidget',
    show: function(barcode){
        this._super({barcode: barcode});
    },
});
gui.define_popup({name:'error-barcode', widget: ErrorBarcodePopupWidget});


var ConfirmPopupWidget = PopupWidget.extend({
    template: 'ConfirmPopupWidget',
});
gui.define_popup({name:'confirm', widget: ConfirmPopupWidget});

/**
 * A popup that allows the user to select one item from a list. 
 *
 * show_popup('selection',{
 *      title: "Popup Title",
 *      list: [
 *          { label: 'foobar',  item: 45 },
 *          { label: 'bar foo', item: 'stuff' },
 *      ],
 *      confirm: function(item) {
 *          // get the item selected by the user.
 *      },
 *      cancel: function(){
 *          // user chose nothing
 *      }
 *  });
 */

var SelectionPopupWidget = PopupWidget.extend({
    template: 'SelectionPopupWidget',
    show: function(options){
        options = options || {};
        var self = this;
        this._super(options);

        this.list    = options.list    || [];
        this.renderElement();
    },
    click_item : function(event) {
        this.gui.close_popup();
        if (this.options.confirm) {
            var item = this.list[parseInt($(event.target).data('item-index'))];
            item = item ? item.item : item;
            this.options.confirm.call(self,item);
        }
    }
});
gui.define_popup({name:'selection', widget: SelectionPopupWidget});


var TextInputPopupWidget = PopupWidget.extend({
    template: 'TextInputPopupWidget',
    show: function(options){
        options = options || {};
        this._super(options);

        this.renderElement();
        this.$('input,textarea').focus();
    },
    click_confirm: function(){
        var value = this.$('input,textarea').val();
        this.gui.close_popup();
        if( this.options.confirm ){
            this.options.confirm.call(this,value);
        }
    },
});
gui.define_popup({name:'textinput', widget: TextInputPopupWidget});


var TextAreaPopupWidget = TextInputPopupWidget.extend({
    template: 'TextAreaPopupWidget',
});
gui.define_popup({name:'textarea', widget: TextAreaPopupWidget});

var PackLotLinePopupWidget = PopupWidget.extend({
    template: 'PackLotLinePopupWidget',
    events: _.extend({}, PopupWidget.prototype.events, {
        'click .remove-lot': 'remove_lot',
        'keydown': 'add_lot',
        'blur .packlot-line-input': 'lose_input_focus'
    }),

    show: function(options){
        this._super(options);
        this.focus();
    },

    click_confirm: function(){
        var pack_lot_lines = this.options.pack_lot_lines;
        this.$('.packlot-line-input').each(function(index, el){
            var cid = $(el).attr('cid'),
                lot_name = $(el).val();
            var pack_line = pack_lot_lines.get({cid: cid});
            pack_line.set_lot_name(lot_name);
        });
        pack_lot_lines.remove_empty_model();
        pack_lot_lines.set_quantity_by_lot();
        this.options.order.save_to_db();
        this.gui.close_popup();
    },

    add_lot: function(ev) {
        if (ev.keyCode === $.ui.keyCode.ENTER){
            var pack_lot_lines = this.options.pack_lot_lines,
                $input = $(ev.target),
                cid = $input.attr('cid'),
                lot_name = $input.val();

            var lot_model = pack_lot_lines.get({cid: cid});
            lot_model.set_lot_name(lot_name);  // First set current model then add new one
            if(!pack_lot_lines.get_empty_model()){
                var new_lot_model = lot_model.add();
                this.focus_model = new_lot_model;
            }
            pack_lot_lines.set_quantity_by_lot();
            this.renderElement();
            this.focus();
        }
    },

    remove_lot: function(ev){
        var pack_lot_lines = this.options.pack_lot_lines,
            $input = $(ev.target).prev(),
            cid = $input.attr('cid');
        var lot_model = pack_lot_lines.get({cid: cid});
        lot_model.remove();
        pack_lot_lines.set_quantity_by_lot();
        this.renderElement();
    },

    lose_input_focus: function(ev){
        var $input = $(ev.target),
            cid = $input.attr('cid');
        var lot_model = this.options.pack_lot_lines.get({cid: cid});
        lot_model.set_lot_name($input.val());
    },

    focus: function(){
        this.$("input[autofocus]").focus();
        this.focus_model = false;   // after focus clear focus_model on widget
    }
});
gui.define_popup({name:'packlotline', widget:PackLotLinePopupWidget});

var NumberPopupWidget = PopupWidget.extend({
    template: 'NumberPopupWidget',
    show: function(options){
        options = options || {};
        this._super(options);

        this.inputbuffer = '' + (options.value   || '');
        this.decimal_separator = _t.database.parameters.decimal_point;
        this.renderElement();
        this.firstinput = true;
    },
    click_numpad: function(event){
        var newbuf = this.gui.numpad_input(
            this.inputbuffer, 
            $(event.target).data('action'), 
            {'firstinput': this.firstinput});

        this.firstinput = (newbuf.length === 0);
        
        if (newbuf !== this.inputbuffer) {
            this.inputbuffer = newbuf;
            this.$('.value').text(this.inputbuffer);
        }
    },
    click_confirm: function(){
        this.gui.close_popup();
        if( this.options.confirm ){
            this.options.confirm.call(this,this.inputbuffer);
        }
    },
});
gui.define_popup({name:'number', widget: NumberPopupWidget});

var PasswordPopupWidget = NumberPopupWidget.extend({
    renderElement: function(){
        this._super();
        this.$('.popup').addClass('popup-password');
    },
    click_numpad: function(event){
        this._super.apply(this, arguments);
        var $value = this.$('.value');
        $value.text($value.text().replace(/./g, '•'));
    },
});
gui.define_popup({name:'password', widget: PasswordPopupWidget});

var OrderImportPopupWidget = PopupWidget.extend({
    template: 'OrderImportPopupWidget',
});
gui.define_popup({name:'orderimport', widget: OrderImportPopupWidget});

/* Popup de pagos */
/* Credit cards popup */
var PaymentExtraInfo = PopupWidget.extend({
    template: 'PaymentExtraInfo',
    show: function(options) {
        var self = this;
        options = options || {};
        this._super(options);
        this.bo_pay_method_id = options.bo_pay_method_id || false;
        this.cashregister = options.cashregister;
        this.payment_screen = options.payment_screen;
        this.mode = options.mode || false;
        this.card_items = options.card_items || [];
        this.exchange_type = options.exchange_type || false;
        //this.deposit_number = this.deposit_number || false;
        this.due = options.due || 0.0;
        let due_usd = (options.due && this.exchange_type && this.exchange_type>0.0) ? this.round_amount(options.due/this.exchange_type) : 0.0;
        due_usd = parseFloat(due_usd.toFixed(3))
        //this.amount = parseFloat(this.round_amount(options.due || 0.0,3).toFixed(3));
        this.due_usd = due_usd;
        //this.amount_usd = due_usd;
        //this.error_msg = false
        this.renderElement();
        let input_focus;
        if (this.mode==='debit' || this.mode==='credit') {
            input_focus = this.$el.find('[name=number]');
        }
        else if (this.mode==='usd_payment') {
            input_focus = this.$el.find('[name=amount_usd]');
        }
        else if (this.mode==='deposit'){
            input_focus = this.$el.find('[name=deposit_number]');
        }
        else if (this.mode==='cheque_payment'){
            input_focus = this.$el.find('[name=cheque_number]');
        }
        if(input_focus){
            input_focus[0].focus();
        }
    },
    events: {
        'click .button_confirm': 'confirm',
        'click .button_close': 'clickClose',
        //'keyup': 'changeAmountUSD',
    },
    // para lueguito xdxd
    // changeAmountUSD: function() {
    // 	var self = this;
    // 	if (this.mode==='usd_payment') {
    // 		let input_usd = this.$el.find('[name=amount_usd]')
    // 		let amount_usd = input_usd.val();
    // 		if (amount_usd === undefined || amount_usd <= 0.0) {
    // 			this.$el.find('.button_confirm').addClass('oe_hidden');
    // 		}
    // 		else{
    // 			this.$el.find('.button_confirm').removeClass('oe_hidden');
    // 		}
    // 	}
    // },
    confirm: function () {
        var self = this;
        let error_msg = false
        let new_pay_line = false
        if (this.mode==='debit' || this.mode==='credit') {
            let amount = this.$el.find('[name=amount]').val(),
                card_number = this.$el.find('[name=number]').val(),
                voucher_ref = this.$el.find('[name=voucher_ref]').val(),
                tag = this.$('.creditcard-detail .credit_card_sel')[0].value;
            
            if (amount === undefined || amount <= 0.0) {
                error_msg = 'Importe ingresado no válido.';
            }
            if (!tag) {
                error_msg = 'No ha seleccionado una tarjeta.';
            }
            if (!card_number) {
                error_msg = 'Debe colocar el número de tarjeta con la que va a registrar el pago.';
            }
            if (!voucher_ref) {
                error_msg = 'No ha ingresado la referencia del Voucher.';
            }
            if (error_msg) {
                return this.launch_error(error_msg)
            }
            amount = this.round_amount(amount);
            new_pay_line = this.add_paymentline(amount);
            new_pay_line.set_credit_card_info(tag);
            new_pay_line.set_card_number(card_number);
            new_pay_line.set_voucher_ref(voucher_ref)
        }
        else if (this.mode==='usd_payment'){
            let amount_usd = this.$el.find('[name=amount_usd]').val();
            
            if (amount_usd === undefined || amount_usd <= 0.0) {
                error_msg = 'Importe ingresado no válido.';
                return this.launch_error(error_msg)
            }
            //this.amount = round_di(parseFloat(value) || 0, this.pos.currency.decimals); 
            let amount = this.round_amount(amount_usd * this.exchange_type);
            new_pay_line = this.add_paymentline(amount);
            new_pay_line.set_exchange_type(this.exchange_type);
            new_pay_line.set_payed_usd(true)
        }
        else if (this.mode==='deposit'){
            let deposit_amount = this.$el.find('[name=deposit_amount]').val();
            let deposit_number = this.$el.find('[name=deposit_number]').val();
            if (!deposit_number) {
                error_msg = 'Ingrese el número de depósito.';
            }
            if (deposit_amount === undefined || deposit_amount <= 0.0) {
                error_msg = 'Importe ingresado no válido.';
            }
            if (error_msg) {
                return this.launch_error(error_msg)
            }
            deposit_amount = this.round_amount(deposit_amount);
            new_pay_line = this.add_paymentline(deposit_amount);
            new_pay_line.set_deposit_number(deposit_number)
        }
        else if (this.mode === 'cheque_payment'){
            let finacial_entity = this.$el.find('[name=finacial_entity]').val(),
                cheque_number = this.$el.find('[name=cheque_number]').val(),
                is_deferred = this.$el.find('[name=is_deferred]').is(':checked'),
                cheque_date_deferred = this.$el.find('[name=cheque_date_deferred]').val(),
                cheque_amount = this.$el.find('[name=cheque_amount]').val();
            
            cheque_amount = parseFloat(cheque_amount)
            if (is_deferred && !cheque_date_deferred) {
                error_msg = 'Coloque la fecha de diferido.';
            }
            if (finacial_entity.length===0 || cheque_number.length===0) {
                error_msg = 'No ha asignado todos los campos.';
            }
            if (cheque_amount <= 0.0 || isNaN(cheque_amount)) {
                error_msg = 'El importe es inválido.';
            }
            if (is_deferred) {
                let def_date = new Date(cheque_date_deferred);
                let today = new Date();
                today = new Date(`${today.getFullYear()}-${today.getMonth()+1}-${today.getDate()}`)
                if (today-def_date <= 0) {
                    error_msg = 'La fecha de diferido debe ser anterior a la fecha actual.';
                }
            }
            if (error_msg) {
                return this.launch_error(error_msg)
            }
            cheque_amount = this.round_amount(cheque_amount);
            new_pay_line = this.add_paymentline(cheque_amount);
            new_pay_line.set_finacial_entity(finacial_entity)
            new_pay_line.set_cheque_number(cheque_number)
            new_pay_line.set_is_deferred(is_deferred)
            new_pay_line.set_cheque_date_deferred(cheque_date_deferred || false)
        }
        this.payment_screen.reset_input();
        this.payment_screen.render_paymentlines();
        this.clickClose()
    },
    add_paymentline: function (amount) {
        amount = typeof amount==='number' ? amount : parseFloat(amount)
        let order = this.pos.get_order();
        let cashregister = this.cashregister;
        order.assert_editable();
        var newPaymentline = new models.Paymentline({},{order: order, cashregister:cashregister, pos: this.pos, amount:amount,bo_pay_method_id:this.bo_pay_method_id});
        if(cashregister.journal.type !== 'cash' || this.pos.config.iface_precompute_cash){
            newPaymentline.set_amount(order.get_due());
            //newPaymentline.set_amount_currency(this.get_amount_currency(order.get_due(),curr_factor));
        }
        order.paymentlines.add(newPaymentline);
        order.select_paymentline(newPaymentline);
        return newPaymentline
    },
    clickClose: function () {
        this.pos.gui.close_popup();
    },
    round_amount: function (amount,decimals) {
        return round_di(parseFloat(amount) || 0, decimals ? decimals : this.pos.currency.decimals);
    },
    // get_amount_currency: function (amount,factor) {
    // 	console.log(amount,factor)
    // 	return parseFloat(this.round_amount(amount * (factor || 1.0)).toFixed(3))
    // },
    launch_error: function (error_msg) {
        this.$el.find('.label_error').addClass('oe_hidden')
        this.$el.find('.errors-container').append(`<span class='label label_error'>${error_msg}</span>`);return;
    }
});

gui.define_popup({ name: 'payment_extra_info', widget: PaymentExtraInfo });


return PopupWidget;
});
