// RGS Template Item client-side script
frappe.ui.form.on('RGS Template Item', {
    refresh: function(frm) {
        // Auto-populate fields when RGS Classification is selected
        if (frm.doc.rgs_classification && !frm.doc.account_name) {
            frappe.db.get_doc('RGS Classification', frm.doc.rgs_classification).then(doc => {
                frm.set_value('account_name', doc.rgs_description);
                frm.set_value('rgs_code', doc.rgs_code);
                if (doc.rgs_account_type) {
                    frm.set_value('account_type', doc.rgs_account_type);
                }
            });
        }
    },
    
    rgs_classification: function(frm) {
        // Auto-populate related fields when RGS Classification changes
        if (frm.doc.rgs_classification) {
            frappe.db.get_doc('RGS Classification', frm.doc.rgs_classification).then(doc => {
                frm.set_value('account_name', doc.rgs_description);
                frm.set_value('rgs_code', doc.rgs_code);
                if (doc.rgs_account_type) {
                    frm.set_value('account_type', doc.rgs_account_type);
                }
                
                // Set mandatory based on RGS level
                if (doc.rgs_nivo <= 3) {
                    frm.set_value('is_mandatory', 1);
                }
            });
        }
    }
});

// Child table script for template items in RGS Template
frappe.ui.form.on('RGS Template Item', {
    rgs_classification: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.rgs_classification) {
            frappe.db.get_doc('RGS Classification', row.rgs_classification).then(doc => {
                frappe.model.set_value(cdt, cdn, 'account_name', doc.rgs_description);
                frappe.model.set_value(cdt, cdn, 'rgs_code', doc.rgs_code);
                if (doc.rgs_account_type) {
                    frappe.model.set_value(cdt, cdn, 'account_type', doc.rgs_account_type);
                }
                
                // Set mandatory based on RGS level
                if (doc.rgs_nivo <= 3) {
                    frappe.model.set_value(cdt, cdn, 'is_mandatory', 1);
                }
            });
        }
    }
});
