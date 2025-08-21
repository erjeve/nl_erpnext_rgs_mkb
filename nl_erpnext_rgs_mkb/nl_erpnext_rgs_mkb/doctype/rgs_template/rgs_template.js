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
            
            frm.add_custom_button(__('Browse RGS Tree'), function() {
                browse_rgs_tree_dialog(frm);
            }, __('Template Builder'));
            
            frm.add_custom_button(__('Import from Template'), function() {
                import_template_dialog(frm);
            }, __('Template Builder'));
        }
        
        // Add template options based on entity type
        add_template_options(frm);
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

function add_template_options(frm) {
    // Add template selection helpers
    if (frm.doc.entity_type) {
        // Filter template items based on entity type and applicable RGS codes
        frm.fields_dict.template_items.grid.get_field('rgs_classification').get_query = function() {
            return {
                filters: {
                    'rgs_status': 'A',
                    'rgs_version': '3.7'
                }
            };
        };
    }
}

function browse_rgs_tree_dialog(frm) {
    // Open RGS tree browser for easy selection
    let dialog = new frappe.ui.Dialog({
        title: __('Browse RGS Classification Tree'),
        size: 'large',
        fields: [
            {
                label: __('Filter by Category'),
                fieldname: 'category_filter',
                fieldtype: 'Select',
                options: '\nBalance Sheet (B)\nProfit & Loss (W)',
                change: function() {
                    let value = dialog.get_value('category_filter');
                    if (value) {
                        let root = value.includes('Balance') ? 'B' : 'W';
                        // Open tree view in a new tab
                        window.open('/app/tree/RGS Classification/' + root);
                    }
                }
            },
            {
                label: __('Instructions'),
                fieldname: 'instructions',
                fieldtype: 'HTML',
                options: '<p>Use the tree view to browse RGS classifications. Click on any classification to add it to your template.</p>'
            }
        ],
        primary_action: function() {
            // Open full tree view
            window.open('/app/tree/RGS Classification');
            dialog.hide();
        },
        primary_action_label: __('Open Full Tree')
    });
    dialog.show();
}

function import_template_dialog(frm) {
    // Import items from another template
    let dialog = new frappe.ui.Dialog({
        title: __('Import from Template'),
        fields: [
            {
                label: __('Source Template'),
                fieldname: 'source_template',
                fieldtype: 'Link',
                options: 'RGS Template',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            'name': ['!=', frm.doc.name],
                            'status': 'Active'
                        }
                    };
                }
            },
            {
                label: __('Import Options'),
                fieldname: 'import_options',
                fieldtype: 'Select',
                options: 'All Items\nMandatory Only\nOptional Only',
                default: 'Mandatory Only',
                reqd: 1
            },
            {
                label: __('Overwrite Existing'),
                fieldname: 'overwrite',
                fieldtype: 'Check',
                default: 0
            }
        ],
        primary_action: function() {
            let values = dialog.get_values();
            if (values) {
                frappe.call({
                    method: 'import_template_items',
                    doc: frm.doc,
                    args: {
                        source_template: values.source_template,
                        import_options: values.import_options,
                        overwrite: values.overwrite
                    },
                    callback: function(r) {
                        if (r.message) {
                            frm.reload_doc();
                            frappe.msgprint(__('Template items imported successfully'));
                            dialog.hide();
                        }
                    }
                });
            }
        },
        primary_action_label: __('Import')
    });
    dialog.show();
}
