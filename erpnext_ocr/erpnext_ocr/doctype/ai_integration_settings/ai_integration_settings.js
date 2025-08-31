// Copyright (c) 2025, John Vincent Fiel and contributors
// For license information, please see license.txt

frappe.ui.form.on('AI Integration Settings', {
    refresh: function(frm) {
        // Add Test Connection button
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Test Connection'), function() {
                test_ai_connection(frm);
            }, __('Actions'));
            
            frm.add_custom_button(__('Test AI Query'), function() {
                show_ai_test_dialog(frm);
            }, __('Actions'));
        }
        
        // Add validation indicators
        if (frm.doc.api_key && frm.doc.ai_provider !== 'Local Model') {
            frm.set_df_property('api_key', 'description', 
                '<span style="color: green;">✓ API Key is set</span>');
        }
        
        // Show/hide fields based on provider
        toggle_provider_fields(frm);
    },
    
    ai_provider: function(frm) {
        toggle_provider_fields(frm);
        
        // Set default model names based on provider
        if (frm.doc.ai_provider === 'OpenAI' && !frm.doc.model_name) {
            frm.set_value('model_name', 'gpt-4-vision-preview');
        } else if (frm.doc.ai_provider === 'Google Gemini' && !frm.doc.model_name) {
            frm.set_value('model_name', 'gemini-pro-vision');
        } else if (frm.doc.ai_provider === 'Anthropic Claude' && !frm.doc.model_name) {
            frm.set_value('model_name', 'claude-3-opus-20240229');
        }
    },
    
    api_key: function(frm) {
        if (frm.doc.api_key) {
            frm.set_df_property('api_key', 'description', 
                '<span style="color: green;">✓ API Key is set</span>');
        } else {
            frm.set_df_property('api_key', 'description', '');
        }
    }
});

function toggle_provider_fields(frm) {
    // Show/hide API key field based on provider
    let show_api_key = frm.doc.ai_provider !== 'Local Model';
    frm.toggle_display('api_key', show_api_key);
    frm.toggle_reqd('api_key', show_api_key);
    
    // Show/hide base URL field
    frm.toggle_display('base_url', frm.doc.ai_provider === 'Local Model' || frm.doc.ai_provider === 'OpenAI');
}

function test_ai_connection(frm) {
    if (!frm.doc.api_key && frm.doc.ai_provider !== 'Local Model') {
        frappe.msgprint(__('Please set API Key first'));
        return;
    }
    
    frappe.show_progress(__('Testing Connection'), 50, 100, __('Connecting to AI provider...'));
    
    frappe.call({
        method: 'test_connection',
        doc: frm.doc,
        callback: function(r) {
            frappe.hide_progress();
            
            if (r.message && r.message.status === 'success') {
                frappe.show_alert({
                    message: __('Connection successful! ✓'),
                    indicator: 'green'
                });
                
                // Show success dialog with option to test AI query
                frappe.confirm(
                    __('Connection test successful! Would you like to test an AI query?'),
                    function() {
                        show_ai_test_dialog(frm);
                    },
                    function() {
                        frappe.msgprint({
                            title: __('Connection Test Successful'),
                            message: __('Your AI integration is working properly. You can now use AI features in OCR Read.'),
                            indicator: 'green'
                        });
                    }
                );
            } else {
                let error_msg = r.message ? r.message.message : 'Unknown error';
                frappe.msgprint({
                    title: __('Connection Failed'),
                    message: __('Error: {0}', [error_msg]),
                    indicator: 'red'
                });
            }
        },
        error: function() {
            frappe.hide_progress();
            frappe.msgprint({
                title: __('Connection Failed'),
                message: __('Unable to connect to AI provider. Please check your settings.'),
                indicator: 'red'
            });
        }
    });
}

function show_ai_test_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Test AI Query'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'info',
                options: `
                    <div class="alert alert-info">
                        <strong>${__('AI Provider')}:</strong> ${frm.doc.ai_provider}<br>
                        <strong>${__('Model')}:</strong> ${frm.doc.model_name || 'Default'}<br>
                        <strong>${__('Status')}:</strong> <span style="color: green;">Connected ✓</span>
                    </div>
                `
            },
            {
                fieldtype: 'Section Break',
                label: __('Test Query')
            },
            {
                fieldtype: 'Select',
                fieldname: 'query_type',
                label: __('Query Type'),
                options: [
                    'Custom Query',
                    'OCR Test',
                    'Classification Test',
                    'Extraction Test'
                ].join('\n'),
                default: 'Custom Query',
                reqd: 1
            },
            {
                fieldtype: 'Long Text',
                fieldname: 'custom_query',
                label: __('Your Question'),
                description: __('Ask anything to test the AI connection'),
                default: 'Hello! Can you help me with document processing?',
                depends_on: 'eval:doc.query_type === "Custom Query"'
            },
            {
                fieldtype: 'HTML',
                fieldname: 'predefined_queries',
                depends_on: 'eval:doc.query_type !== "Custom Query"',
                options: get_predefined_query_html()
            },
            {
                fieldtype: 'Section Break',
                label: __('Response')
            },
            {
                fieldtype: 'Long Text',
                fieldname: 'ai_response',
                label: __('AI Response'),
                read_only: 1
            },
            {
                fieldtype: 'HTML',
                fieldname: 'usage_info',
                options: '<div id="usage-info"></div>'
            }
        ],
        primary_action_label: __('Send Query'),
        primary_action: function(values) {
            send_test_query(frm, dialog, values);
        },
        secondary_action_label: __('Clear Response'),
        secondary_action: function() {
            dialog.set_value('ai_response', '');
            $('#usage-info').html('');
        }
    });
    
    dialog.show();
    
    // Update query when type changes
    dialog.fields_dict.query_type.$input.on('change', function() {
        update_query_content(dialog);
    });
}

function get_predefined_query_html() {
    return `
        <div class="predefined-queries">
            <h5>${__('Predefined Test Queries')}</h5>
            <div class="alert alert-warning">
                <small>${__('These queries will test specific AI capabilities without requiring an image.')}</small>
            </div>
        </div>
    `;
}

function update_query_content(dialog) {
    let query_type = dialog.get_value('query_type');
    let predefined_queries = {
        'OCR Test': 'Explain how OCR (Optical Character Recognition) works and what types of documents it can process.',
        'Classification Test': 'List the common types of business documents that can be automatically classified, such as invoices, receipts, purchase orders, etc.',
        'Extraction Test': 'Describe what structured data can typically be extracted from a business invoice, including field names and data types.'
    };
    
    if (query_type in predefined_queries) {
        dialog.set_value('custom_query', predefined_queries[query_type]);
    }
}

function send_test_query(frm, dialog, values) {
    let query = values.custom_query;
    if (!query || query.trim() === '') {
        frappe.msgprint(__('Please enter a query'));
        return;
    }
    
    // Show loading state
    dialog.set_value('ai_response', __('Processing your query...'));
    dialog.get_primary_btn().prop('disabled', true);
    
    frappe.call({
        method: 'erpnext_ocr.erpnext_ocr.doctype.ai_integration_settings.ai_integration_settings.test_ai_query',
        args: {
            settings_name: frm.doc.name,
            query: query,
            query_type: values.query_type
        },
        callback: function(r) {
            dialog.get_primary_btn().prop('disabled', false);
            
            if (r.message && r.message.status === 'success') {
                dialog.set_value('ai_response', r.message.response);
                
                // Show usage information
                if (r.message.usage) {
                    let usage_html = `
                        <div class="usage-info" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                            <h6>${__('Usage Information')}</h6>
                            <small>
                                <strong>${__('Tokens Used')}:</strong> ${r.message.usage.total_tokens || 'N/A'}<br>
                                <strong>${__('Model')}:</strong> ${r.message.model || 'N/A'}<br>
                                <strong>${__('Response Time')}:</strong> ${r.message.response_time || 'N/A'}
                            </small>
                        </div>
                    `;
                    $('#usage-info').html(usage_html);
                }
                
                frappe.show_alert({
                    message: __('Query processed successfully!'),
                    indicator: 'green'
                });
            } else {
                let error_msg = r.message ? r.message.message : 'Unknown error';
                dialog.set_value('ai_response', __('Error: {0}', [error_msg]));
                
                frappe.show_alert({
                    message: __('Query failed: {0}', [error_msg]),
                    indicator: 'red'
                });
            }
        },
        error: function() {
            dialog.get_primary_btn().prop('disabled', false);
            dialog.set_value('ai_response', __('Error: Unable to process query'));
            
            frappe.show_alert({
                message: __('Query processing failed'),
                indicator: 'red'
            });
        }
    });
}