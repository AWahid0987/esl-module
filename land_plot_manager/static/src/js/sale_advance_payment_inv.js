odoo.define('land_plot_manager.sale_advance_payment_inv', function (require) {
    'use strict';
    
    console.log('=== sale_advance_payment_inv.js file loaded ===');
    
    var FormController = require('web.FormController');
    var FormRenderer = require('web.FormRenderer');
    var rpc = require('web.rpc');
    
    FormRenderer.include({
        _renderField: function (node) {
            var result = this._super.apply(this, arguments);
            var self = this;
            
            if (node.attrs.name === 'custom_method') {
                setTimeout(function() {
                    self._updateCustomMethodOptions();
                }, 300);
                setTimeout(function() {
                    self._updateCustomMethodOptions();
                }, 800);
                setTimeout(function() {
                    self._updateCustomMethodOptions();
                }, 1500);
            }
            
            if (node.attrs.name === 'sale_order_id' || node.attrs.name === 'plan_type_for_selection') {
                setTimeout(function() {
                    if (self._updateCustomMethodOptions) {
                        self._updateCustomMethodOptions();
                    }
                }, 500);
            }
            
            return result;
        },
        
        _updateCustomMethodOptions: function () {
            var self = this;
            var record = this.state;
            
            if (!record || !record.data) {
                return;
            }
            
            // First try to get plan_type from plan_type_for_selection field
            var planType = '';
            if (record.data.plan_type_for_selection) {
                planType = record.data.plan_type_for_selection;
                console.log('Got plan_type from plan_type_for_selection:', planType);
            }
            
            // If not found, get from sale_order_id
            if (!planType || planType === '') {
                var saleOrderId = record.data.sale_order_id;
                console.log('sale_order_id:', saleOrderId);
                
                if (!saleOrderId) {
                    console.log('No sale_order_id found');
                    // Try to get from DOM directly
                    var $planTypeField = $('[name="plan_type_for_selection"]');
                    if ($planTypeField.length) {
                        planType = $planTypeField.val() || '';
                        console.log('Got plan_type from DOM:', planType);
                        if (planType) {
                            self._updateOptionsBasedOnPlanType(planType);
                            return;
                        }
                    }
                    return;
                }
                
                var saleOrderResId = saleOrderId.resId || saleOrderId;
                if (!saleOrderResId) {
                    console.log('No saleOrderResId found');
                    return;
                }
                
                console.log('Fetching plan_type from sale.order, ID:', saleOrderResId);
                rpc.query({
                    model: 'sale.order',
                    method: 'read',
                    args: [[saleOrderResId], ['plan_type']],
                }).then(function(result) {
                    console.log('RPC result:', result);
                    if (result && result.length > 0) {
                        planType = result[0].plan_type || '';
                        console.log('Got plan_type from RPC:', planType);
                        self._updateOptionsBasedOnPlanType(planType);
                    } else {
                        console.log('No plan_type in RPC result');
                    }
                }).catch(function(error) {
                    console.error('RPC Error:', error);
                });
            } else {
                console.log('Using plan_type from field:', planType);
                self._updateOptionsBasedOnPlanType(planType);
            }
        },
        
        _updateOptionsBasedOnPlanType: function (planType) {
            var self = this;
            var standardPlans = ['full', 'installment'];
            // Only show all 6 options if planType is exactly 'full' or 'installment'
            // For Navy plans or any other plan type, show only 3 options
            var shouldShowAll = (planType === 'full' || planType === 'installment');
            
            console.log('Plan Type:', planType, 'Should show 6 options:', shouldShowAll);
            
            // If planType is empty, default to hiding extra options (Navy behavior)
            if (!planType || planType === '') {
                console.log('Plan Type is empty, defaulting to 3 options');
                shouldShowAll = false;
            }
            
            // Find all radio buttons with name="custom_method" - search in entire document/form
            var $radios = $('input[type="radio"][name="custom_method"]');
            
            // If not found, try searching in the renderer's element
            if (!$radios.length && self.$el) {
                $radios = self.$el.find('input[type="radio"][name="custom_method"]');
            }
            
            // If still not found, try searching in the form
            if (!$radios.length) {
                $radios = $('form').find('input[type="radio"][name="custom_method"]');
            }
            
            // If still not found, try searching in modal/dialog
            if (!$radios.length) {
                $radios = $('.modal, .o_dialog').find('input[type="radio"][name="custom_method"]');
            }
            
            console.log('Found radio buttons:', $radios.length);
            
            if (!$radios.length) {
                console.log('No radio buttons found for custom_method');
                return;
            }
            
            var foundCount = 0;
            var hiddenCount = 0;
            
            $radios.each(function() {
                var $input = $(this);
                var value = $input.val();
                
                console.log('Processing radio button with value:', value);
                
                // Find the label/parent container - try multiple methods
                var $container = $input.closest('label');
                if (!$container.length || $container.length === 0) {
                    $container = $input.closest('.custom-control');
                }
                if (!$container.length || $container.length === 0) {
                    $container = $input.closest('.o_radio_item');
                }
                if (!$container.length || $container.length === 0) {
                    $container = $input.closest('div[class*="radio"]');
                }
                if (!$container.length || $container.length === 0) {
                    $container = $input.closest('div');
                }
                if (!$container.length || $container.length === 0) {
                    $container = $input.parent();
                }
                
                // If still no container, use the input itself
                if (!$container.length || $container.length === 0) {
                    $container = $input;
                }
                
                console.log('Container found:', $container.length > 0, 'Value:', value);
                
                // Standard plans: show all 6 options (regular, down_payment, confirmation, installment, ballot, possession)
                // Navy plans: show only 3 options (regular, down_payment, installment)
                if (value === 'confirmation' || value === 'ballot' || value === 'possession') {
                    if (shouldShowAll) {
                        // Show for standard plans
                        $container.show();
                        $container.css('display', '');
                        $container.removeClass('d-none');
                        $input.prop('disabled', false);
                        $input.prop('readonly', false);
                        $input.removeAttr('disabled');
                        foundCount++;
                        console.log('Showing option:', value);
                    } else {
                        // Hide for Navy plans - use multiple methods
                        $container.hide();
                        $container.css({
                            'display': 'none !important',
                            'visibility': 'hidden',
                            'opacity': '0',
                            'height': '0',
                            'width': '0',
                            'overflow': 'hidden'
                        });
                        $container.addClass('d-none o_hidden');
                        $input.prop('disabled', true);
                        $input.prop('readonly', true);
                        $input.attr('disabled', 'disabled');
                        $input.css('display', 'none');
                        // Also hide any associated text/labels
                        $container.find('span, label').hide();
                        hiddenCount++;
                        console.log('Hiding option:', value, 'Container:', $container.length);
                    }
                } else if (value === 'down_payment' || value === 'regular' || value === 'installment') {
                    // Always show these 3 options
                    $container.show();
                    $container.css('display', '');
                    $container.removeClass('d-none');
                    $input.prop('disabled', false);
                    $input.prop('readonly', false);
                    $input.removeAttr('disabled');
                    foundCount++;
                    console.log('Showing option:', value);
                }
            });
            
            console.log('Total Found:', foundCount, 'Hidden:', hiddenCount);
        }
    });
    
    FormController.include({
        start: function () {
            var result = this._super.apply(this, arguments);
            var self = this;
            
            // Run multiple times to ensure it works
            var timeouts = [300, 500, 800, 1000, 1500, 2000, 3000];
            timeouts.forEach(function(delay) {
                setTimeout(function() {
                    if (self.renderer && self.renderer._updateCustomMethodOptions) {
                        self.renderer._updateCustomMethodOptions();
                    }
                }, delay);
            });
            
            // Also set up an interval to keep checking (in case DOM updates slowly)
            var checkInterval = setInterval(function() {
                if (self.renderer && self.renderer._updateCustomMethodOptions) {
                    var hasRadios = $('input[type="radio"][name="custom_method"]').length > 0;
                    if (hasRadios) {
                        self.renderer._updateCustomMethodOptions();
                        // Clear interval after 10 seconds to avoid infinite checking
                        setTimeout(function() {
                            clearInterval(checkInterval);
                        }, 10000);
                    }
                }
            }, 500);
            
            return result;
        },
        
        _onFieldChanged: function (event) {
            this._super.apply(this, arguments);
            
            if (event.data && event.data.changes) {
                var changes = event.data.changes;
                // Update when sale_order_id, plan_type_for_selection, or custom_method changes
                if (changes.sale_order_id || changes.plan_type_for_selection || changes.custom_method) {
                    var self = this;
                    setTimeout(function() {
                        if (self.renderer && self.renderer._updateCustomMethodOptions) {
                            self.renderer._updateCustomMethodOptions();
                        }
                    }, 300);
                }
            }
        }
    });
});
