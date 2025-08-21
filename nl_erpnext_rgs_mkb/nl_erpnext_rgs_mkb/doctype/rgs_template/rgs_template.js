// Copyright (c) 2025, Your Organization and contributors
// For license information, please see license.txt

frappe.ui.form.on('RGS Template', {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Generate CoA'), function() {
                generate_coa_dialog(frm);
            }, __('Actions'));
            
            frm.add_custom_button(__('Load Default Codes'), function() {
                load_default_codes(frm);
            }, __('Actions'));
        }
    },
    
    entity_type: function(frm) {
        if (frm.doc.entity_type) {
            // Auto-populate template name
            if (!frm.doc.template_name) {
                frm.set_value('template_name', frm.doc.entity_type + '_Standard');
            }
            
            // Load applicable RGS codes
            load_rgs_codes_for_entity(frm);
        }
    }
});

function generate_coa_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Generate Chart of Accounts'),
        fields: [
            {
                label: __('Company'),
                fieldname: 'company',
                fieldtype: 'Link',
                options: 'Company',
                reqd: 1
            },
            {
                label: __('Overwrite Existing'),
                fieldname: 'overwrite',
                fieldtype: 'Check',
                default: 0,
                description: __('Check to overwrite existing accounts with same RGS codes')
            }
        ],
        primary_action: function() {
            let values = dialog.get_values();
            if (values) {
                frappe.call({
                    method: 'generate_chart_of_accounts',
                    doc: frm.doc,
                    args: {
                        company: values.company
                    },
                    callback: function(r) {
                        if (r.message) {
                            let result = r.message;
                            let message = `<h4>Chart of Accounts Generated</h4>
                                         <p><strong>Created:</strong> ${result.total_created} accounts</p>`;
                            
                            if (result.errors && result.errors.length > 0) {
                                message += `<p><strong>Errors:</strong></p><ul>`;
                                result.errors.forEach(error => {
                                    message += `<li>${error}</li>`;
                                });
                                message += `</ul>`;
                            }
                            
                            frappe.msgprint({
                                title: __('Generation Complete'),
                                indicator: 'green',
                                message: message
                            });
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

function load_default_codes(frm) {
    if (!frm.doc.entity_type) {
        frappe.msgprint(__('Please select Entity Type first'));
        return;
    }
    
    frappe.call({
        method: 'nl_erpnext_rgs_mkb.nl_erpnext_rgs_mkb.utils.get_default_rgs_codes_for_entity',
        args: {
            entity_type: frm.doc.entity_type
        },
        callback: function(r) {
            if (r.message) {
                frm.clear_table('rgs_codes');
                r.message.forEach(function(code) {
                    let row = frm.add_child('rgs_codes');
                    row.rgs_code = code.rgs_code;
                    row.description = code.description;
                    row.nivo = code.nivo;
                    row.is_included = 1;
                });
                frm.refresh_field('rgs_codes');
                frappe.msgprint(__('Default RGS codes loaded successfully'));
            }
        }
    });
}

function load_rgs_codes_for_entity(frm) {
    if (!frm.doc.entity_type) return;
    
    // Auto-set description based on entity type
    let descriptions = {
        'ZZP': 'Standard Chart of Accounts for ZZP (Zelfstandig Zonder Personeel)',
        'EZ': 'Standard Chart of Accounts for Eenmanszaak / VOF',
        'BV': 'Standard Chart of Accounts for Besloten Vennootschap',
        'SVC': 'Standard Chart of Accounts for Stichting / Vereniging / Coöperatie'
    };
    
    if (!frm.doc.description && descriptions[frm.doc.entity_type]) {
        frm.set_value('description', descriptions[frm.doc.entity_type]);
    }
}
