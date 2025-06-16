//Validación del formulario de registro
document.getElementById('registerForm').addEventListener('submit', function(e) {
    const password = document.getElementById('reg_password').value;
    const confirm = document.getElementById('reg_confirm').value;
    const email = document.getElementById('reg_email').value;
    const name = document.getElementById('reg_name').value;
    const terms = document.getElementById('terms').checked;

    let hasErrors = false;

    // Validar nombre
    if (name.trim().length < 2) {
        showError('reg_name', 'El nombre debe tener al menos 2 caracteres');
        hasErrors = true;
    }

    // Validar email
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
        showError('reg_email', 'Formato de email inválido');
        hasErrors = true;
    }

    // Validar contraseña
    if (password.length < 8) {
        showError('reg_password', 'La contraseña debe tener al menos 8 caracteres');
        hasErrors = true;
    }

    // Validar confirmación
    if (password !== confirm) {
        showError('reg_confirm', 'Las contraseñas no coinciden');
        hasErrors = true;
    }

    // Validar términos
    if (!terms) {
        alert('Debes aceptar los términos y condiciones');
        hasErrors = true;
    }

    if (hasErrors) {
        e.preventDefault();
        return false;
    }
});
document.addEventListener('DOMContentLoaded', function () {
    const regEmail = document.getElementById('reg_email');
    const regPassword = document.getElementById('reg_password');
    const regConfirm = document.getElementById('reg_confirm');
    const regPhone = document.getElementById('reg_phone');
    const regName = document.getElementById('reg_name');

    regEmail?.addEventListener('blur', function () {
        const email = this.value;
        const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!pattern.test(email)) {
            showError('reg_email', 'Formato de email inválido');
        } else {
            showSuccess('reg_email', 'Email válido');
        }
    });

    regPassword?.addEventListener('input', function () {
        const pwd = this.value;
        const strength = calculatePasswordStrength(pwd);
        updatePasswordStrength(strength);

        if (pwd.length < 8) {
            showError('reg_password', 'La contraseña debe tener al menos 8 caracteres');
        } else {
            hideError('reg_password');
        }
    });

    regConfirm?.addEventListener('input', function () {
        if (this.value !== regPassword.value) {
            showError('reg_confirm', 'Las contraseñas no coinciden');
        } else {
            showSuccess('reg_confirm', 'Las contraseñas coinciden');
        }
    });

    regPhone?.addEventListener('blur', function () {
        const pattern = /^(\+57\s?)?[3][0-9]{2}\s?[0-9]{3}\s?[0-9]{4}$/;
        if (this.value && !pattern.test(this.value.replace(/\s/g, ''))) {
            showError('reg_phone', 'Teléfono inválido (ej: +57 300 123 4567)');
        } else {
            hideError('reg_phone');
        }
    });

    regName?.addEventListener('blur', function () {
        if (this.value.trim().length < 2) {
            showError('reg_name', 'El nombre debe tener al menos 2 caracteres');
        } else {
            hideError('reg_name');
        }
    });
});

function showError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.getElementById(fieldId + '_error');
    const successDiv = document.getElementById(fieldId + '_success');
    if (field) {
        field.classList.add('error');
        field.classList.remove('success');
    }
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
    if (successDiv) successDiv.style.display = 'none';
}

function showSuccess(fieldId, message) {
    const field = document.getElementById(fieldId);
    const successDiv = document.getElementById(fieldId + '_success');
    const errorDiv = document.getElementById(fieldId + '_error');
    if (field) {
        field.classList.remove('error');
        field.classList.add('success');
    }
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
    }
    if (errorDiv) errorDiv.style.display = 'none';
}

function hideError(fieldId) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.getElementById(fieldId + '_error');
    if (field) field.classList.remove('error');
    if (errorDiv) errorDiv.style.display = 'none';
}

function calculatePasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;
    return strength;
}

function updatePasswordStrength(strength) {
    const fill = document.getElementById('strength-fill');
    const text = document.getElementById('strength-text');
    if (!fill || !text) return;

    fill.className = 'strength-fill';
    switch (strength) {
        case 0:
        case 1:
            fill.classList.add('strength-weak');
            text.textContent = 'Muy débil';
            text.style.color = '#e74c3c';
            break;
        case 2:
            fill.classList.add('strength-fair');
            text.textContent = 'Débil';
            text.style.color = '#f39c12';
            break;
        case 3:
            fill.classList.add('strength-good');
            text.textContent = 'Buena';
            text.style.color = '#f1c40f';
            break;
        default:
            fill.classList.add('strength-strong');
            text.textContent = 'Fuerte';
            text.style.color = '#27ae60';
            break;
    }
}
