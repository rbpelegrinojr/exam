/* main.js — Exam Management System */

// ============================================================
// Sidebar toggle
// ============================================================
document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.getElementById('sidebarToggle');
    const wrapper = document.getElementById('wrapper');
    if (toggleBtn && wrapper) {
        toggleBtn.addEventListener('click', function () {
            wrapper.classList.toggle('sidebar-collapsed');
        });
    }

    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert.alert-success').forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // File upload: show selected file names
    const fileInput = document.getElementById('scan_images');
    if (fileInput) {
        fileInput.addEventListener('change', function () {
            const count = this.files.length;
            const label = document.querySelector('#uploadArea p');
            if (label && count > 0) {
                label.textContent = count === 1
                    ? `Selected: ${this.files[0].name}`
                    : `${count} file(s) selected`;
            }
        });
    }

    // Question type selector — show/hide relevant hints
    const typeSelect = document.getElementById('questionTypeSelect');
    if (typeSelect) {
        typeSelect.addEventListener('change', function () {
            updateTypeHint(this.value);
        });
        updateTypeHint(typeSelect.value);
    }
});

// ============================================================
// Question type hint
// ============================================================
function updateTypeHint(type) {
    const hints = {
        multiple_choice:     'Students select one of four options (A, B, C, D).',
        modified_true_false: 'Students mark True or False and write corrections.',
        essay:               'Open-ended — teacher scores via score grid (1–10).',
        coding:              'Programming task — teacher scores via score grid (1–10).',
    };
    let hint = document.getElementById('typeHint');
    if (!hint) {
        hint = document.createElement('div');
        hint.id = 'typeHint';
        hint.className = 'form-text text-info mt-1';
        const select = document.getElementById('questionTypeSelect');
        if (select) select.parentNode.appendChild(hint);
    }
    hint.textContent = hints[type] || '';
}

// ============================================================
// Confirm delete dialogs
// ============================================================
function confirmDelete(itemType) {
    return window.confirm(`Are you sure you want to delete this ${itemType}? This action cannot be undone.`);
}

// ============================================================
// Upload progress
// ============================================================
function showProgress() {
    const progress = document.getElementById('uploadProgress');
    if (progress) {
        progress.classList.remove('d-none');
    }
    // Disable submit button to prevent double-submit
    const form = document.getElementById('uploadForm');
    if (form) {
        const btn = form.querySelector('button[type="submit"]');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Uploading...';
        }
    }
    return true;
}

// ============================================================
// Select all / deselect all students
// ============================================================
function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('.student-cb:not(:disabled)');
    const btn = document.getElementById('selectAllBtn');
    if (!btn) return;
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    checkboxes.forEach(cb => {
        cb.checked = !allChecked;
    });
    btn.textContent = allChecked ? 'Select All' : 'Deselect All';
}
