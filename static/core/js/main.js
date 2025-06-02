// main.js - Arquivo principal de JavaScript para o sistema de gestão de condomínios

$(document).ready(function() {
    // Inicializações básicas quando o documento está pronto

    // 1. Ativa tooltips do Bootstrap
    $('[data-toggle="tooltip"]').tooltip();

    // 2. Configurações para datatables (se estiver usando)
    if ($.fn.DataTable) {
        $('.datatable').DataTable({
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.10.25/i18n/Portuguese-Brasil.json"
            },
            "responsive": true
        });
    }

    // 3. Validação de formulários
    $('form.needs-validation').on('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });

    // 4. Máscaras para campos (usando jQuery Mask Plugin)
    if ($.fn.mask) {
        $('.cpf-mask').mask('000.000.000-00');
        $('.phone-mask').mask('(00) 00000-0000');
        $('.money-mask').mask('000.000.000.000.000,00', {reverse: true});
    }

    // 5. Confirmação para ações importantes
    $('.btn-confirm').on('click', function() {
        return confirm('Tem certeza que deseja realizar esta ação?');
    });

    // 6. Inicialização do AdminLTE (se estiver usando)
    if ($.AdminLTE) {
        $.AdminLTE.init();
    }
});

// Funções úteis que podem ser usadas em todo o sistema
function formatarMoeda(valor) {
    return valor.toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    });
}

function mostrarCarregamento() {
    $('#loading-overlay').fadeIn();
}

function esconderCarregamento() {
    $('#loading-overlay').fadeOut();
}

// AJAX global setup
$.ajaxSetup({
    headers: {
        'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
    },
    beforeSend: function() {
        mostrarCarregamento();
    },
    complete: function() {
        esconderCarregamento();
    }
});
