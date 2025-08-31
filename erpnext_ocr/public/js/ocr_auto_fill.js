// OCR Auto Fill Script
// This script automatically fills new documents with OCR data when routed from OCR Read

frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        fill_ocr_data_if_available(frm, 'Sales Invoice');
    }
});

frappe.ui.form.on('Purchase Invoice', {
    onload: function(frm) {
        fill_ocr_data_if_available(frm, 'Purchase Invoice');
    }
});

frappe.ui.form.on('Sales Order', {
    onload: function(frm) {
        fill_ocr_data_if_available(frm, 'Sales Order');
    }
});

frappe.ui.form.on('Purchase Order', {
    onload: function(frm) {
        fill_ocr_data_if_available(frm, 'Purchase Order');
    }
});

frappe.ui.form.on('Quotation', {
    onload: function(frm) {
        fill_ocr_data_if_available(frm, 'Quotation');
    }
});

function fill_ocr_data_if_available(frm, doctype) {
    // Only fill for new documents
    if (frm.doc.__islocal) {
        const ocr_data_key = 'ocr_data_' + doctype;
        const ocr_data_str = localStorage.getItem(ocr_data_key);
        
        if (ocr_data_str) {
            try {
                const ocr_data = JSON.parse(ocr_data_str);
                
                // Clear the localStorage item
                localStorage.removeItem(ocr_data_key);
                
                // Show notification
                frappe.show_alert({
                    message: __('Filling document with OCR data from {0}', [ocr_data.source_ocr_doc]),
                    indicator: 'blue'
                });
                
                // Fill the form fields
                fill_form_with_ocr_data(frm, ocr_data);
                
                // Add OCR info banner
                add_ocr_info_banner(frm, ocr_data);
                
            } catch (e) {
                console.error('Error parsing OCR data:', e);
                localStorage.removeItem(ocr_data_key);
            }
        }
    }
}

function fill_form_with_ocr_data(frm, ocr_data) {
    // Fill mapped fields
    if (ocr_data.mapped_fields) {
        Object.keys(ocr_data.mapped_fields).forEach(function(fieldname) {
            const field_data = ocr_data.mapped_fields[fieldname];
            
            if (frm.fields_dict[fieldname]) {
                try {
                    // Handle different field types
                    let value = field_data.value;
                    
                    // Date fields
                    if (field_data.fieldtype === 'Date' && typeof value === 'string') {
                        // Frappe expects date in YYYY-MM-DD format
                        value = frappe.datetime.user_to_str(value);
                    }
                    
                    // Set the field value
                    frm.set_value(fieldname, value);
                    
                } catch (e) {
                    console.warn('Could not set field', fieldname, ':', e);
                }
            }
        });
    }
    
    // Fill items if available
    if (ocr_data.items_data && ocr_data.items_data.length > 0 && frm.fields_dict.items) {
        // Clear existing items
        frm.clear_table('items');
        
        // Add OCR items
        ocr_data.items_data.forEach(function(item_data) {
            const item_row = frm.add_child('items');
            
            Object.keys(item_data).forEach(function(fieldname) {
                if (item_row[fieldname] !== undefined) {
                    try {
                        item_row[fieldname] = item_data[fieldname];
                    } catch (e) {
                        console.warn('Could not set item field', fieldname, ':', e);
                    }
                }
            });
        });
        
        // Refresh items table
        frm.refresh_field('items');
    }
    
    // Refresh the form
    frm.refresh();
}

function add_ocr_info_banner(frm, ocr_data) {
    // Add an info banner about OCR source
    const banner_html = `
        <div class="alert alert-info" style="margin: 10px 0;">
            <strong><i class="fa fa-eye"></i> OCR Data Filled</strong><br>
            <small>
                Source: ${ocr_data.source_ocr_doc} | 
                Confidence: ${(ocr_data.confidence * 100).toFixed(1)}% | 
                Fields Mapped: ${Object.keys(ocr_data.mapped_fields || {}).length} |
                Items: ${(ocr_data.items_data || []).length}
            </small>
            <button class="btn btn-xs btn-default pull-right" onclick="$(this).parent().hide()">
                <i class="fa fa-times"></i>
            </button>
        </div>
    `;
    
    // Add banner to form
    if (frm.layout && frm.layout.wrapper) {
        $(frm.layout.wrapper).find('.form-layout').prepend(banner_html);
    }
    
    // Add custom button to view original OCR document
    frm.add_custom_button(__('View OCR Source'), function() {
        frappe.set_route('Form', 'OCR Read', ocr_data.source_ocr_doc);
    }, __('OCR'));
    
    // Add button to show raw OCR text
    if (ocr_data.raw_ocr_text) {
        frm.add_custom_button(__('View OCR Text'), function() {
            show_ocr_text_dialog(ocr_data.raw_ocr_text);
        }, __('OCR'));
    }
}

function show_ocr_text_dialog(ocr_text) {
    const dialog = new frappe.ui.Dialog({
        title: __('Original OCR Text'),
        size: 'large',
        fields: [
            {
                fieldtype: 'Text',
                fieldname: 'ocr_text',
                label: __('Extracted Text'),
                default: ocr_text,
                read_only: 1
            }
        ]
    });
    
    dialog.show();
}