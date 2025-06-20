/**
 * Main JavaScript file for Audit Management System
 * Contains global functions and utilities used across the application
 */

$(document).ready(function() {
    // Initialize global components
    initializeTooltips();
    initializeFormValidation();
    initializeFileUpload();
    initializeDatepickers();
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        $('.alert-dismissible').fadeOut('slow');
    }, 5000);
    
    // Initialize search functionality
    initializeSearch();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    // Add custom validation styles
    $('form').on('submit', function(e) {
        var form = this;
        if (form.checkValidity() === false) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.classList.add('was-validated');
    });
    
    // Real-time validation for specific fields
    $('.form-control[required]').on('blur', function() {
        if (!this.value.trim()) {
            $(this).addClass('is-invalid');
        } else {
            $(this).removeClass('is-invalid').addClass('is-valid');
        }
    });
}

/**
 * Initialize file upload handlers
 */
function initializeFileUpload() {
    $('.file-upload').on('change', function() {
        var file = this.files[0];
        var $input = $(this);
        var maxSize = $input.data('max-size') || 10485760; // 10MB default
        
        if (file) {
            // Check file size
            if (file.size > maxSize) {
                showAlert('error', 'File size exceeds maximum allowed size');
                this.value = '';
                return;
            }
            
            // Show file name
            var fileName = file.name;
            $input.next('.file-upload-info').text(fileName);
        }
    });
}

/**
 * Initialize date pickers
 */
function initializeDatepickers() {
    // By default, allow future dates unless restricted explicitly
    $('input[type="date"]').each(function () {
        // Only restrict future dates for fields with this class
        if ($(this).hasClass("restrict-future")) {
            $(this).attr("max", new Date().toISOString().split("T")[0]);
        } else {
            $(this).removeAttr("max"); // ensure future dates are enabled
        }
    });
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    // Global search with debounce
    let searchTimeout;
    $('#globalSearch').on('input', function() {
        clearTimeout(searchTimeout);
        const query = $(this).val();
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => {
                performGlobalSearch(query);
            }, 300);
        }
    });
}

/**
 * Perform global search across entities
 */
function performGlobalSearch(query) {
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
        });
}

/**
 * Display search results
 */
function displaySearchResults(results) {
    const $resultsContainer = $('#searchResults');
    $resultsContainer.empty();
    
    if (results.length === 0) {
        $resultsContainer.html('<p class="text-muted">No results found</p>');
        return;
    }
    
    results.forEach(result => {
        const $item = $(`
            <div class="search-result-item p-2 border-bottom">
                <strong>${result.title}</strong>
                <br><small class="text-muted">${result.type} - ${result.description}</small>
            </div>
        `);
        $item.on('click', () => {
            window.location.href = result.url;
        });
        $resultsContainer.append($item);
    });
}

/**
 * Format currency for Indian locale
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '₹0.00';
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

/**
 * Format date for display
 */
function formatDate(dateString, format = 'DD/MM/YYYY') {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN');
}

/**
 * Show alert message
 */
function showAlert(type, message, title = '') {
    const alertClass = type === 'error' ? 'danger' : type;
    const alertHtml = `
        <div class="alert alert-${alertClass} alert-dismissible fade show" role="alert">
            ${title ? `<strong>${title}</strong><br>` : ''}
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insert at top of main content area
    $('main .container-fluid').prepend(alertHtml);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        $('.alert').last().fadeOut();
    }, 5000);
}

/**
 * Confirm action with user
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('success', 'Copied to clipboard');
    }).catch(() => {
        showAlert('error', 'Failed to copy to clipboard');
    });
}

/**
 * Export table to CSV
 */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = Array.from(table.querySelectorAll('tr'));
    
    const csvContent = rows.map(row => {
        const cells = Array.from(row.querySelectorAll('th, td'));
        return cells.map(cell => {
            // Clean cell content and escape commas
            const text = cell.textContent.trim().replace(/"/g, '""');
            return `"${text}"`;
        }).join(',');
    }).join('\n');
    
    downloadCSV(csvContent, filename);
}

/**
 * Download CSV content
 */
function downloadCSV(csvContent, filename) {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

/**
 * Validate PAN number format
 */
function validatePAN(pan) {
    const panRegex = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
    return panRegex.test(pan);
}

/**
 * Validate GSTIN format
 */
function validateGSTIN(gstin) {
    const gstinRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
    return gstinRegex.test(gstin);
}

/**
 * Validate email format
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Auto-format PAN input
 */
$(document).on('input', 'input[name="pan"], #pan', function() {
    let value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (value.length > 10) value = value.substring(0, 10);
    this.value = value;
    
    // Validate format
    if (value.length === 10) {
        if (validatePAN(value)) {
            $(this).removeClass('is-invalid').addClass('is-valid');
        } else {
            $(this).removeClass('is-valid').addClass('is-invalid');
        }
    }
});

/**
 * Auto-format GSTIN input
 */
$(document).on('input', 'input[name="gstin"], #gstin', function() {
    let value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (value.length > 15) value = value.substring(0, 15);
    this.value = value;
    
    // Validate format
    if (value.length === 15) {
        if (validateGSTIN(value)) {
            $(this).removeClass('is-invalid').addClass('is-valid');
        } else {
            $(this).removeClass('is-valid').addClass('is-invalid');
        }
    }
});

/**
 * Auto-format phone number
 */
$(document).on('input', 'input[name="phone"], input[type="tel"]', function() {
    let value = this.value.replace(/[^0-9]/g, '');
    if (value.length > 10) value = value.substring(0, 10);
    this.value = value;
});

/**
 * Print functionality
 */
function printElement(elementId) {
    const element = document.getElementById(elementId);
    const printWindow = window.open('', '', 'height=600,width=800');
    
    printWindow.document.write('<html><head><title>Print</title>');
    printWindow.document.write('<link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">');
    printWindow.document.write('</head><body>');
    printWindow.document.write(element.innerHTML);
    printWindow.document.write('</body></html>');
    
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
}

/**
 * Loading state management
 */
function showLoading(element) {
    const $element = $(element);
    $element.prop('disabled', true);
    const originalText = $element.text();
    $element.data('original-text', originalText);
    $element.html('<i class="fas fa-spinner fa-spin me-2"></i>Loading...');
}

function hideLoading(element) {
    const $element = $(element);
    $element.prop('disabled', false);
    const originalText = $element.data('original-text');
    $element.html(originalText);
}

/**
 * Form auto-save functionality
 */
function initAutoSave(formId, saveUrl) {
    const form = document.getElementById(formId);
    let saveTimeout;
    
    $(form).on('input change', function() {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            autoSaveForm(form, saveUrl);
        }, 2000); // Save after 2 seconds of inactivity
    });
}

function autoSaveForm(form, saveUrl) {
    const formData = new FormData(form);
    
    fetch(saveUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Draft saved automatically', '');
        }
    })
    .catch(error => {
        console.error('Auto-save failed:', error);
    });
}

/**
 * Initialize keyboard shortcuts
 */
$(document).on('keydown', function(e) {
    // Ctrl+S to save form
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const $form = $('form:visible').first();
        if ($form.length) {
            $form.submit();
        }
    }
    
    // Ctrl+N to create new (if button exists)
    if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        const $newBtn = $('[data-bs-toggle="modal"]:contains("New"), .btn:contains("Add"):first');
        if ($newBtn.length) {
            $newBtn.click();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        $('.modal.show').modal('hide');
    }
});

/**
 * Client search functionality with autocomplete
 */
function initClientSearch(inputId, resultsId) {
    const $input = $('#' + inputId);
    const $results = $('#' + resultsId);
    let searchTimeout;
    
    $input.on('input', function() {
        clearTimeout(searchTimeout);
        const query = $(this).val();
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => {
                fetch(`/api/clients/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(clients => {
                        displayClientResults(clients, $results);
                    });
            }, 300);
        } else {
            $results.empty().hide();
        }
    });
    
    // Hide results when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('#' + inputId + ', #' + resultsId).length) {
            $results.hide();
        }
    });
}

function displayClientResults(clients, $container) {
    $container.empty();
    
    if (clients.length === 0) {
        $container.hide();
        return;
    }
    
    clients.forEach(client => {
        const $item = $(`
            <div class="search-result-item p-2 border-bottom cursor-pointer">
                <strong>${client.name}</strong>
                ${client.pan ? `<br><small class="text-muted">PAN: ${client.pan}</small>` : ''}
            </div>
        `);
        
        $item.on('click', () => {
            selectClient(client);
            $container.hide();
        });
        
        $container.append($item);
    });
    
    $container.show();
}

function selectClient(client) {
    // Override in specific pages
    console.log('Client selected:', client);
}

/**
 * Financial calculations helper
 */
const FinanceCalculator = {
    calculateTax: function(income, taxSlabs) {
        let tax = 0;
        let remainingIncome = income;
        
        for (let slab of taxSlabs) {
            if (remainingIncome <= 0) break;
            
            const taxableAmount = Math.min(remainingIncome, slab.limit - slab.from);
            tax += taxableAmount * (slab.rate / 100);
            remainingIncome -= taxableAmount;
        }
        
        return tax;
    },
    
    calculateGST: function(amount, rate) {
        return amount * (rate / 100);
    },
    
    calculateTDS: function(amount, rate) {
        return amount * (rate / 100);
    }
};

/**
 * Utility functions for common operations
 */
const Utils = {
    generateInvoiceNumber: function(prefix = 'INV') {
        const timestamp = Date.now().toString().slice(-8);
        return `${prefix}-${timestamp}`;
    },
    
    calculateDaysDifference: function(date1, date2) {
        const diffTime = Math.abs(date2 - date1);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    },
    
    isOverdue: function(dueDate) {
        return new Date(dueDate) < new Date();
    },
    
    capitalizeWords: function(str) {
        return str.replace(/\w\S*/g, (txt) => {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    }
};

// Export functions for use in other scripts
window.AuditApp = {
    formatCurrency,
    formatDate,
    showAlert,
    confirmAction,
    copyToClipboard,
    exportTableToCSV,
    validatePAN,
    validateGSTIN,
    validateEmail,
    printElement,
    showLoading,
    hideLoading,
    FinanceCalculator,
    Utils
};
