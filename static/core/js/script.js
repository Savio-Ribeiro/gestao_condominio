/**
 * script.js - Arquivo principal de JavaScript para o sistema de gestão de condomínios
 * Contém funções essenciais para operação do sistema
 */

// Configuração inicial quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // 1. Inicializa componentes do sistema
    initComponents();

    // 2. Configura eventos globais
    setupGlobalEvents();

    // 3. Carrega dados iniciais se necessário
    loadInitialData();
});

/**
 * Inicializa todos os componentes necessários
 */
function initComponents() {
    // Tooltips do Bootstrap
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Datepickers (usando flatpickr como exemplo)
    if (typeof flatpickr !== 'undefined') {
        flatpickr('.datepicker', {
            dateFormat: 'd/m/Y',
            locale: 'pt'
        });
    }

    // Máscaras de campos (usando vanilla-masker como exemplo)
    if (typeof VMasker !== 'undefined') {
        VMasker(document.querySelector('.cpf')).maskPattern('999.999.999-99');
        VMasker(document.querySelector('.phone')).maskPattern('(99) 99999-9999');
        VMasker(document.querySelector('.money')).maskMoney({
            precision: 2,
            separator: ',',
            delimiter: '.',
            unit: 'R$'
        });
    }
}

/**
 * Configura eventos globais do sistema
 */
function setupGlobalEvents() {
    // Validação de formulários
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Confirmação para ações importantes
    document.querySelectorAll('.btn-confirm').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja realizar esta ação?')) {
                e.preventDefault();
            }
        });
    });

    // Menu ativo baseado na URL
    highlightActiveMenu();
}

/**
 * Carrega dados iniciais se necessário
 */
function loadInitialData() {
    // Exemplo: Carrega avisos do condomínio
    if (document.getElementById('avisos-container')) {
        fetchAvisos();
    }

    // Exemplo: Carrega contas pendentes
    if (document.getElementById('contas-pendentes')) {
        fetchContasPendentes();
    }
}

/**
 * Destaca o item de menu ativo
 */
function highlightActiveMenu() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            const parentMenu = link.closest('.has-treeview');
            if (parentMenu) {
                parentMenu.classList.add('menu-open');
                parentMenu.querySelector('.nav-link:first-child').classList.add('active');
            }
        }
    });
}

/**
 * Funções utilitárias
 */

// Formata valor monetário
function formatMoney(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Mostra loader global
function showLoader() {
    document.getElementById('global-loader').style.display = 'flex';
}

// Esconde loader global
function hideLoader() {
    document.getElementById('global-loader').style.display = 'none';
}

// Configuração AJAX global
if (typeof axios !== 'undefined') {
    axios.interceptors.request.use(config => {
        showLoader();
        const token = document.querySelector('meta[name="csrf-token"]').content;
        if (token) {
            config.headers['X-CSRF-TOKEN'] = token;
        }
        return config;
    });

    axios.interceptors.response.use(response => {
        hideLoader();
        return response;
    }, error => {
        hideLoader();
        showError(error.response.data.message || 'Erro na requisição');
        return Promise.reject(error);
    });
}

/**
 * Exibe mensagem de erro
 */
function showError(message) {
    const toast = document.getElementById('errorToast');
    if (toast) {
        const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toast);
        toast.querySelector('.toast-body').textContent = message;
        toastBootstrap.show();
    } else {
        alert(message);
    }
}

/**
 * Funções específicas do módulo de avisos
 */
async function fetchAvisos() {
    try {
        const response = await fetch('/api/avisos');
        const avisos = await response.json();
        renderAvisos(avisos);
    } catch (error) {
        showError('Falha ao carregar avisos');
    }
}

function renderAvisos(avisos) {
    const container = document.getElementById('avisos-container');
    if (container) {
        container.innerHTML = avisos.map(aviso => `
            <div class="aviso-card">
                <h5>${aviso.titulo}</h5>
                <p>${aviso.descricao}</p>
                <small>${new Date(aviso.data).toLocaleDateString('pt-BR')}</small>
            </div>
        `).join('');
    }
}

/**
 * Funções específicas do módulo financeiro
 */
async function fetchContasPendentes() {
    try {
        const response = await fetch('/api/contas/pendentes');
        const contas = await response.json();
        renderContasPendentes(contas);
    } catch (error) {
        showError('Falha ao carregar contas pendentes');
    }
}

function renderContasPendentes(contas) {
    const container = document.getElementById('contas-pendentes');
    if (container) {
        container.innerHTML = contas.map(conta => `
            <tr>
                <td>${conta.descricao}</td>
                <td>${conta.vencimento}</td>
                <td class="text-danger">${formatMoney(conta.valor)}</td>
                <td>
                    <button class="btn btn-sm btn-primary btn-pagar" data-id="${conta.id}">
                        Registrar Pagamento
                    </button>
                </td>
            </tr>
        `).join('');

        // Adiciona eventos aos botões
        document.querySelectorAll('.btn-pagar').forEach(btn => {
            btn.addEventListener('click', handlePagamento);
        });
    }
}

async function handlePagamento(event) {
    const contaId = event.target.dataset.id;
    try {
        const response = await fetch(`/api/contas/pagar/${contaId}`, {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            fetchContasPendentes(); // Recarrega a lista
            showSuccess('Pagamento registrado com sucesso!');
        }
    } catch (error) {
        showError('Falha ao registrar pagamento');
    }
}

function showSuccess(message) {
    const toast = document.getElementById('successToast');
    if (toast) {
        const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toast);
        toast.querySelector('.toast-body').textContent = message;
        toastBootstrap.show();
    } else {
        alert(message);
    }
}
