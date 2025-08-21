// Copyright (c) 2025, Your Organization and contributors
// For license information, please see license.txt

frappe.ui.form.on('RGS Classification', {
    refresh: function(frm) {
        // Add custom buttons
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Create Account'), function() {
                create_account_dialog(frm);
            }, __('Actions'));
            
            frm.add_custom_button(__('Generate CoA for Entity'), function() {
                generate_coa_dialog(frm);
            }, __('Actions'));
            
            frm.add_custom_button(__('Select for Template'), function() {
                select_for_template_dialog(frm);
            }, __('Template'));
        }
        
        // Set field properties based on nivo
        set_field_properties(frm);
        
        // Add tree view filters
        add_tree_filters(frm);
    },
    
    rgs_nivo: function(frm) {
        set_field_properties(frm);
        
        // Auto-set is_group based on nivo
        if (frm.doc.rgs_nivo < 5) {
            frm.set_value('is_group', 1);
        } else {
            frm.set_value('is_group', 0);
        }
    },
    
    rgs_code: function(frm) {
        // Auto-determine account type based on RGS code
        if (frm.doc.rgs_code) {
            if (frm.doc.rgs_code.startsWith('B')) {
                if (frm.doc.rgs_code.includes('Iva') || frm.doc.rgs_code.includes('Mva')) {
                    frm.set_value('account_type', 'Asset');
                } else if (frm.doc.rgs_code.includes('Eiv')) {
                    frm.set_value('account_type', 'Equity');
                } else if (frm.doc.rgs_code.includes('Las') || frm.doc.rgs_code.includes('Kre')) {
                    frm.set_value('account_type', 'Liability');
                }
            } else if (frm.doc.rgs_code.startsWith('W')) {
                if (frm.doc.rgs_code.includes('Omz')) {
                    frm.set_value('account_type', 'Income');
                } else {
                    frm.set_value('account_type', 'Expense');
                }
            }
        }
    }
});

function set_field_properties(frm) {
    // Show/hide fields based on nivo level
    if (frm.doc.rgs_nivo <= 2) {
        frm.set_df_property('balance_must_be', 'hidden', 1);
        frm.set_df_property('account_type', 'reqd', 0);
    } else {
        frm.set_df_property('balance_must_be', 'hidden', 0);
        frm.set_df_property('account_type', 'reqd', 1);
    }
}

function create_account_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Create Account'),
        fields: [
            {
                label: __('Company'),
                fieldname: 'company',
                fieldtype: 'Link',
                options: 'Company',
                reqd: 1
            }
        ],
        primary_action: function() {
            let values = dialog.get_values();
            if (values) {
                frappe.call({
                    method: 'create_account',
                    doc: frm.doc,
                    args: {
                        company: values.company
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(__('Account created successfully'));
                            dialog.hide();
                        }
                    }
                });
            }
        },
        primary_action_label: __('Create')
    });
    dialog.show();
}

function generate_coa_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Generate Chart of Accounts for Entity'),
        fields: [
            {
                label: __('Company'),
                fieldname: 'company',
                fieldtype: 'Link',
                options: 'Company',
                reqd: 1
            },
            {
                label: __('Entity Type'),
                fieldname: 'entity_type',
                fieldtype: 'Select',
                options: 'ZZP\nEZ\nBV\nSVC',
                reqd: 1,
                default: 'ZZP'
            }
        ],
        primary_action: function() {
            let values = dialog.get_values();
            if (values) {
                frappe.call({
                    method: 'generate_chart_for_entity',
                    doc: frm.doc,
                    args: {
                        entity_type: values.entity_type,
                        company: values.company
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(__('Chart of Accounts generated successfully'));
                            dialog.hide();
                        }
                    }
                });
            }
        },
        primary_action_label: __('Generate')
    });
    dialog.show();
}

function add_tree_filters(frm) {
    // Add tree view filters for better navigation
    if (frm.doc.__islocal) return;
    
    // Add filter buttons in tree view
    frm.page.add_inner_button(__('Balance Sheet'), function() {
        frappe.set_route('Tree', 'RGS Classification', 'B');
    }, __('Quick Navigate'));
    
    frm.page.add_inner_button(__('P&L'), function() {
        frappe.set_route('Tree', 'RGS Classification', 'W');
    }, __('Quick Navigate'));
}

function select_for_template_dialog(frm) {
    // Dialog to select this RGS code for a template
    let dialog = new frappe.ui.Dialog({
        title: __('Add to Template'),
        fields: [
            {
                label: __('Template'),
                fieldname: 'template',
                fieldtype: 'Link',
                options: 'RGS Template',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            'status': 'Active'
                        }
                    };
                }
            },
            {
                label: __('Account Name'),
                fieldname: 'account_name',
                fieldtype: 'Data',
                reqd: 1,
                default: frm.doc.rgs_description
            },
            {
                label: __('Account Type'),
                fieldname: 'account_type',
                fieldtype: 'Select',
                options: 'Asset\nLiability\nEquity\nIncome\nExpense',
                reqd: 1,
                default: frm.doc.rgs_account_type
            }
        ],
        primary_action: function() {
            let values = dialog.get_values();
            if (values) {
                frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
                            doctype: 'RGS Template Item',
                            parent: values.template,
                            parenttype: 'RGS Template',
                            parentfield: 'template_items',
                            rgs_classification: frm.doc.name,
                            account_name: values.account_name,
                            account_type: values.account_type,
                            rgs_code: frm.doc.rgs_code,
                            is_mandatory: 1
                        }
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(__('Added to template successfully'));
                            dialog.hide();
                        }
                    }
                });
            }
        },
        primary_action_label: __('Add to Template')
    });
    dialog.show();
}
