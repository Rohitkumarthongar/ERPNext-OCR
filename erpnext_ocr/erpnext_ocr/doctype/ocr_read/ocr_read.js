// Copyright (c) 2025, John Vincent Fiel and contributors
// For license information, please see license.txt

frappe.ui.form.on('OCR Read', {
    refresh: function(frm) {
        // Set up image preview
        if (frm.doc.file_to_read) {
            frm.set_df_property('image_preview', 'options', get_image_preview_html(frm.doc.file_to_read));
        }
        
        // Add custom buttons
        if (frm.doc.suggested_doctype && frm.doc.ai_result) {
            frm.add_custom_button(__('Create Document'), function() {
                show_document_creation_dialog(frm);
            }, __('Actions'));
        }
        
        if (frm.doc.ai_result) {
            frm.add_custom_button(__('View AI Data'), function() {
                show_ai_data_dialog(frm);
            }, __('Actions'));
        }
    },
    
    file_to_read: function(frm) {
        if (frm.doc.file_to_read) {
            frm.set_df_property('image_preview', 'options', get_image_preview_html(frm.doc.file_to_read));
            frm.refresh_field('image_preview');
        }
    },
    
    read_image: function(frm) {
        if (!frm.doc.file_to_read) {
            frappe.msgprint(__('Please select a file first'));
            return;
        }
        
        frappe.show_progress(__('Processing'), 50, 100, __('Reading file with OCR...'));
        
        frappe.call({
            method: 'read_image',
            doc: frm.doc,
            callback: function(r) {
                frappe.hide_progress();
                console.log('OCR processing response:', r);
                
                if (r.message) {
                    if (r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('OCR processing completed successfully'),
                            indicator: 'green'
                        });
                        frm.refresh();
                    } else if (r.message.status === 'warning') {
                        frappe.show_alert({
                            message: __('OCR processing completed with warnings'),
                            indicator: 'orange'
                        });
                        frm.refresh();
                    }
                } else {
                    frappe.msgprint(__('OCR processing failed - no response'));
                }
            },
            error: function(r) {
                frappe.hide_progress();
                console.error('OCR processing error:', r);
                let error_msg = 'Unknown error';
                if (r.responseJSON && r.responseJSON.message) {
                    error_msg = r.responseJSON.message;
                } else if (r.message) {
                    error_msg = r.message;
                }
                frappe.msgprint(__('Error processing file: {0}', [error_msg]));
            }
        });
    },
    
    read_with_ai: function(frm) {
        if (!frm.doc.file_to_read) {
            frappe.msgprint(__('Please select a file first'));
            return;
        }
        
        frappe.show_progress(__('Processing'), 30, 100, __('Processing file with AI...'));
        
        frappe.call({
            method: 'read_with_ai',
            doc: frm.doc,
            callback: function(r) {
                frappe.hide_progress();
                console.log('AI processing response:', r);
                
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: __('AI processing completed successfully'),
                        indicator: 'green'
                    });
                    frm.refresh();
                    
                    // Show AI data in a dialog
                    show_ai_data_dialog(frm);
                } else {
                    frappe.msgprint(__('AI processing failed or returned no data'));
                }
            },
            error: function(r) {
                frappe.hide_progress();
                console.error('AI processing error:', r);
                let error_msg = 'Unknown error';
                if (r.responseJSON && r.responseJSON.message) {
                    error_msg = r.responseJSON.message;
                } else if (r.message) {
                    error_msg = r.message;
                }
                frappe.msgprint(__('Error processing file with AI: {0}', [error_msg]));
            }
        });
    },
    
    classify_document: function(frm) {
        if (!frm.doc.file_to_read) {
            frappe.msgprint(__('Please select a file first'));
            return;
        }
        
        frappe.show_progress(__('Classifying'), 50, 100, __('Analyzing document type...'));
        
        frappe.call({
            method: 'classify_document',
            doc: frm.doc,
            callback: function(r) {
                frappe.hide_progress();
                console.log('Classification response:', r);
                
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: __('Document classification completed'),
                        indicator: 'green'
                    });
                    frm.refresh();
                    
                    // Show classification results
                    show_classification_results(frm, r.message.classification);
                } else {
                    frappe.msgprint(__('Document classification failed'));
                }
            },
            error: function(r) {
                frappe.hide_progress();
                console.error('Classification error:', r);
                let error_msg = 'Unknown error';
                if (r.responseJSON && r.responseJSON.message) {
                    error_msg = r.responseJSON.message;
                } else if (r.message) {
                    error_msg = r.message;
                }
                frappe.msgprint(__('Error classifying document: {0}', [error_msg]));
            }
        });
    },
    
    proceed_with_doctype: function(frm) {
        if (!frm.doc.detected_document_type && !frm.doc.suggested_doctype) {
            frappe.msgprint(__('Please run document classification first to detect document type'));
            return;
        }
        
        frappe.show_progress(__('Preparing Document'), 50, 100, __('Processing OCR data...'));
        
        frappe.call({
            method: 'proceed_with_doctype',
            doc: frm.doc,
            callback: function(r) {
                frappe.hide_progress();
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });
                    
                    // Store OCR data in localStorage for the new document
                    localStorage.setItem('ocr_data_' + r.message.doctype, JSON.stringify(r.message.ocr_data));
                    
                    // Navigate to new document with OCR data
                    frappe.set_route('Form', r.message.doctype, 'new');
                    
                } else {
                    frappe.msgprint(__('Failed to prepare document data. Please check the error logs.'));
                }
            },
            error: function(r) {
                frappe.hide_progress();
                frappe.msgprint(__('Error preparing document: {0}', [r.message || 'Unknown error']));
            }
        });
    },
    
    preview_document_creation: function(frm) {
        if (!frm.doc.detected_document_type && !frm.doc.suggested_doctype) {
            frappe.msgprint(__('Please run document classification first to detect document type'));
            return;
        }
        
        frappe.show_progress(__('Generating Preview'), 30, 100, __('Analyzing data...'));
        
        frappe.call({
            method: 'preview_document_creation',
            doc: frm.doc,
            callback: function(r) {
                frappe.hide_progress();
                console.log('Preview response:', r);
                
                if (r.message) {
                    if (r.message.status === 'success') {
                        show_document_preview_dialog(frm, r.message);
                    } else {
                        frappe.msgprint(__('Preview Error: {0}', [r.message.message || 'Unknown error']));
                    }
                } else {
                    frappe.msgprint(__('Failed to generate preview - no response received'));
                }
            },
            error: function(r) {
                frappe.hide_progress();
                console.error('Preview error:', r);
                let error_msg = 'Unknown error';
                if (r.responseJSON && r.responseJSON.message) {
                    error_msg = r.responseJSON.message;
                } else if (r.message) {
                    error_msg = r.message;
                }
                frappe.msgprint(__('Error generating preview: {0}', [error_msg]));
            }
        });
    }
});

function get_image_preview_html(file_url) {
    if (!file_url) return '';
    
    return `
        <div style="text-align: center; margin: 10px 0; padding: 10px; border: 1px solid #e0e0e0; border-radius: 4px;">
            <img src="${file_url}" style="max-width: 100%; max-height: 300px; border-radius: 4px;" />
            <p style="margin-top: 10px; font-size: 12px; color: #666;">
                <strong>File:</strong> ${file_url.split('/').pop()}
            </p>
        </div>
    `;
}

function show_ai_data_dialog(frm) {
    if (!frm.doc.ai_result) {
        frappe.msgprint(__('No AI data available'));
        return;
    }
    
    let ai_data;
    try {
        ai_data = JSON.parse(frm.doc.ai_result);
    } catch (e) {
        ai_data = { raw_data: frm.doc.ai_result };
    }
    
    let dialog = new frappe.ui.Dialog({
        title: __('AI Extracted Data'),
        size: 'large',
        fields: [
            {
                fieldtype: 'JSON',
                fieldname: 'ai_data',
                label: __('Extracted Data'),
                default: JSON.stringify(ai_data, null, 2),
                read_only: 1
            }
        ]
    });
    
    dialog.show();
}

function show_classification_results(frm, classification) {
    let message = `
        <div style="padding: 15px;">
            <h4>${__('Document Classification Results')}</h4>
            <table class="table table-bordered" style="margin-top: 10px;">
                <tr>
                    <td><strong>${__('Document Type')}</strong></td>
                    <td>${classification.document_type || 'Unknown'}</td>
                </tr>
                <tr>
                    <td><strong>${__('Confidence')}</strong></td>
                    <td>${((classification.confidence || 0) * 100).toFixed(1)}%</td>
                </tr>
                <tr>
                    <td><strong>${__('Suggested DocType')}</strong></td>
                    <td>${classification.suggested_doctype || 'None'}</td>
                </tr>
            </table>
        </div>
    `;
    
    frappe.msgprint({
        title: __('Classification Results'),
        message: message,
        indicator: 'green'
    });
}

function show_document_preview_dialog(frm, data) {
    let preview_html = `
        <div class="document-preview">
            <div class="alert alert-info">
                <strong>${__('Document Type')}:</strong> ${data.doctype}<br>
                <strong>${__('Confidence')}:</strong> ${(data.confidence * 100).toFixed(1)}%<br>
                <strong>${__('Fields Mapped')}:</strong> ${data.mapped_fields_count} / ${data.total_fields}<br>
                <strong>${__('Items Found')}:</strong> ${data.items_count}
            </div>
            
            <h5>${__('Document Fields Preview')}</h5>
            <table class="table table-bordered table-sm">
                <thead>
                    <tr>
                        <th>${__('Field')}</th>
                        <th>${__('Value')}</th>
                        <th>${__('Status')}</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add field previews
    Object.keys(data.preview_data).forEach(function(fieldname) {
        let field = data.preview_data[fieldname];
        let status_badge = field.mapped ? 
            '<span class="badge badge-success">Mapped</span>' : 
            '<span class="badge badge-secondary">Default</span>';
        
        preview_html += `
            <tr>
                <td><strong>${field.label}</strong></td>
                <td>${field.value}</td>
                <td>${status_badge}</td>
            </tr>
        `;
    });
    
    preview_html += '</tbody></table>';
    
    // Add items preview if available
    if (data.items_preview && data.items_preview.length > 0) {
        preview_html += `<h5>${__('Items Preview')}</h5>`;
        preview_html += '<table class="table table-bordered table-sm"><thead><tr>';
        
        // Get item field headers
        let item_fields = [];
        if (data.items_preview[0]) {
            Object.keys(data.items_preview[0]).forEach(function(key) {
                if (key !== 'row_index') {
                    item_fields.push(key);
                    preview_html += `<th>${data.items_preview[0][key].label || key}</th>`;
                }
            });
        }
        preview_html += '</tr></thead><tbody>';
        
        // Add item rows
        data.items_preview.forEach(function(item) {
            preview_html += '<tr>';
            item_fields.forEach(function(field) {
                if (item[field]) {
                    preview_html += `<td>${item[field].value}</td>`;
                } else {
                    preview_html += '<td>-</td>';
                }
            });
            preview_html += '</tr>';
        });
        
        preview_html += '</tbody></table>';
    }
    
    preview_html += '</div>';
    
    let dialog = new frappe.ui.Dialog({
        title: __('Document Creation Preview'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'preview_content',
                options: preview_html
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldtype: 'Select',
                fieldname: 'target_doctype',
                label: __('Change Document Type'),
                options: data.available_doctypes.map(dt => dt.name).join('\n'),
                default: data.doctype
            }
        ],
        primary_action_label: __('Create Document'),
        primary_action: function(values) {
            dialog.hide();
            
            // Create document with selected doctype
            frappe.call({
                method: 'proceed_with_doctype',
                doc: frm.doc,
                args: {
                    target_doctype: values.target_doctype
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'green'
                        });
                        
                        frappe.confirm(
                            __('Document created successfully. Open it now?'),
                            function() {
                                frappe.set_route('Form', r.message.doctype, r.message.name);
                            }
                        );
                    }
                }
            });
        },
        secondary_action_label: __('Refresh Preview'),
        secondary_action: function(values) {
            dialog.hide();
            
            // Refresh preview with new doctype
            frappe.call({
                method: 'preview_document_creation',
                doc: frm.doc,
                args: {
                    target_doctype: values.target_doctype
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        show_document_preview_dialog(frm, r.message);
                    }
                }
            });
        }
    });
    
    dialog.show();
}

function show_document_creation_dialog(frm, data) {
    if (!data) {
        frappe.call({
            method: 'proceed_with_doctype',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    show_document_creation_dialog(frm, r.message);
                }
            }
        });
        return;
    }
    
    let dialog = new frappe.ui.Dialog({
        title: __('Create Document from OCR Data'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'info',
                options: `
                    <div class="alert alert-info">
                        <strong>${__('Detected Document Type')}:</strong> ${data.detected_type || 'Unknown'}<br>
                        <strong>${__('Confidence')}:</strong> ${((data.confidence || 0) * 100).toFixed(1)}%
                    </div>
                `
            },
            {
                fieldtype: 'Link',
                fieldname: 'target_doctype',
                label: __('Target DocType'),
                options: 'DocType',
                default: data.suggested_doctype,
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            'issingle': 0,
                            'istable': 0,
                            'disabled': 0
                        }
                    };
                }
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldtype: 'HTML',
                fieldname: 'field_mapping',
                label: __('Field Mapping'),
                options: '<div id="field-mapping-container"></div>'
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldtype: 'JSON',
                fieldname: 'ai_data_preview',
                label: __('AI Extracted Data'),
                default: data.ai_data,
                read_only: 1
            }
        ],
        primary_action_label: __('Create Document'),
        primary_action: function(values) {
            create_document_from_ai_data(frm, values, dialog);
        }
    });
    
    dialog.show();
    
    // Update field mapping when doctype changes
    dialog.fields_dict.target_doctype.$input.on('change', function() {
        update_field_mapping(dialog, data.ai_data);
    });
    
    // Initial field mapping
    if (data.suggested_doctype) {
        setTimeout(() => {
            update_field_mapping(dialog, data.ai_data);
        }, 500);
    }
}

function update_field_mapping(dialog, ai_data) {
    let target_doctype = dialog.get_value('target_doctype');
    if (!target_doctype || !ai_data) return;
    
    frappe.model.with_doctype(target_doctype, function() {
        let meta = frappe.get_meta(target_doctype);
        let ai_fields = [];
        
        try {
            let parsed_data = JSON.parse(ai_data);
            ai_fields = Object.keys(parsed_data);
        } catch (e) {
            ai_fields = ['extracted_text'];
        }
        
        let mapping_html = '<h5>' + __('Field Mapping') + '</h5>';
        mapping_html += '<table class="table table-bordered">';
        mapping_html += '<thead><tr><th>' + __('AI Field') + '</th><th>' + __('Target Field') + '</th></tr></thead>';
        mapping_html += '<tbody>';
        
        ai_fields.forEach(function(ai_field) {
            mapping_html += '<tr>';
            mapping_html += '<td>' + ai_field + '</td>';
            mapping_html += '<td><select class="form-control field-mapping-select" data-ai-field="' + ai_field + '">';
            mapping_html += '<option value="">' + __('-- Select Field --') + '</option>';
            
            meta.fields.forEach(function(field) {
                if (field.fieldtype !== 'Table' && field.fieldtype !== 'HTML' && field.fieldtype !== 'Button') {
                    mapping_html += '<option value="' + field.fieldname + '">' + field.label + ' (' + field.fieldname + ')</option>';
                }
            });
            
            mapping_html += '</select></td>';
            mapping_html += '</tr>';
        });
        
        mapping_html += '</tbody></table>';
        
        $('#field-mapping-container').html(mapping_html);
    });
}

function create_document_from_ai_data(frm, values, dialog) {
    // Collect field mapping
    let field_mapping = {};
    $('.field-mapping-select').each(function() {
        let ai_field = $(this).data('ai-field');
        let target_field = $(this).val();
        if (target_field) {
            field_mapping[ai_field] = target_field;
        }
    });
    
    frappe.call({
        method: 'erpnext_ocr.erpnext_ocr.doctype.ocr_read.ocr_read.create_document_from_ocr',
        args: {
            ocr_read_name: frm.doc.name,
            target_doctype: values.target_doctype,
            field_mapping: field_mapping
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                dialog.hide();
                frappe.msgprint({
                    title: __('Success'),
                    message: r.message.message,
                    indicator: 'green'
                });
                
                // Ask if user wants to open the created document
                frappe.confirm(
                    __('Document created successfully. Do you want to open it?'),
                    function() {
                        frappe.set_route('Form', r.message.doctype, r.message.name);
                    }
                );
            }
        }
    });
}