// ============================================
// Dayflow HRMS - Main JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initFormValidation();
    initToasts();
    initModals();
    initDataTables();
});

// ========== Form Validation ==========
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Basic client-side validation
            const inputs = form.querySelectorAll('[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    showError(input, 'This field is required');
                } else {
                    clearError(input);
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

function showError(input, message) {
    const formGroup = input.parentElement;
    const errorElement = formGroup.querySelector('.form-error') || document.createElement('div');
    errorElement.className = 'form-error';
    errorElement.textContent = message;
    
    if (!formGroup.querySelector('.form-error')) {
        formGroup.appendChild(errorElement);
    }
    
    input.style.borderColor = 'var(--error)';
}

function clearError(input) {
    const formGroup = input.parentElement;
    const errorElement = formGroup.querySelector('.form-error');
    
    if (errorElement) {
        errorElement.remove();
    }
    
    input.style.borderColor = '';
}

// ========== Toast Notifications ==========
function initToasts() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} animate-fadeIn`;
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== Modal Dialogs ==========
function initModals() {
    const modalOverlays = document.querySelectorAll('.modal-overlay');
    
    modalOverlays.forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeModal(overlay);
            }
        });
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modal) {
    if (typeof modal === 'string') {
        modal = document.getElementById(modal);
    }
    
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// ========== Data Tables ==========
function initDataTables() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        addTableSearch(table);
        addTableSort(table);
    });
}

function addTableSearch(table) {
    const searchInput = table.parentElement.querySelector('.table-search');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const filter = this.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    }
}

function addTableSort(table) {
    const headers = table.querySelectorAll('th[data-sortable]');
    
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(table, header.cellIndex);
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    let ascending = true;
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        if (ascending) {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// ========== Attendance Functions ==========
function checkIn() {
    const form = document.getElementById('checkin-form');
    if (form) {
        form.submit();
    }
}

function checkOut() {
    if (confirm('Are you sure you want to check out?')) {
        const form = document.getElementById('checkout-form');
        if (form) {
            form.submit();
        }
    }
}

// ========== Leave Request Functions ==========
function calculateLeaveDays() {
    const startDate = document.getElementById('id_start_date');
    const endDate = document.getElementById('id_end_date');
    const daysDisplay = document.getElementById('leave-days');
    
    if (startDate && endDate && daysDisplay) {
        const start = new Date(startDate.value);
        const end = new Date(endDate.value);
        
        if (start && end && end >= start) {
            const days = Math.floor((end - start) / (1000 * 60 * 60 * 24)) + 1;
            daysDisplay.textContent = `Total days: ${days}`;
        }
    }
}

// ========== Admin Functions ==========
function confirmLeaveAction(action, leaveId) {
    const message = action === 'approve' ? 
        'Are you sure you want to approve this leave request?' :
        'Are you sure you want to reject this leave request?';
    
    if (confirm(message)) {
        openModal('leave-action-modal-' + leaveId);
    }
}

function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// ========== Real-time Updates ==========
function updateAttendanceStatus() {
    // This would be enhanced with WebSockets for real-time updates
    // For now, we'll use simple polling
    const statusDisplay = document.getElementById('attendance-status');
    
    if (statusDisplay) {
        setInterval(() => {
            // Fetch current status via AJAX
            // For demo, we'll just update the time
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            
            const timeDisplay = document.getElementById('current-time');
            if (timeDisplay) {
                timeDisplay.textContent = timeString;
            }
        }, 1000);
    }
}

// Initialize real-time updates
updateAttendanceStatus();

// ========== Utility Functions ==========
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatTime(time) {
    return new Date(time).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}
