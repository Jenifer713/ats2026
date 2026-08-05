/* ═══════════════════════════════════════════════════════
   ATS RECLUTA — JavaScript principal
   Sistema de Reclutamiento y Selección de Talento
═══════════════════════════════════════════════════════ */

/* ─── Sidebar toggle (mobile) ───────────────────────── */
(function () {
  'use strict';

  const sidebar  = document.getElementById('sidebar');
  const toggle   = document.getElementById('sidebar-toggle');
  const mainContent = document.getElementById('main-content');

  // Crear overlay dinámicamente
  let overlay = document.getElementById('sidebar-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'sidebar-overlay';
    document.body.appendChild(overlay);
  }

  function openSidebar() {
    sidebar && sidebar.classList.add('open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar && sidebar.classList.remove('open');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  toggle && toggle.addEventListener('click', function () {
    sidebar && sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
  });
  overlay.addEventListener('click', closeSidebar);

  // Cerrar sidebar al navegar (mobile)
  document.querySelectorAll('#sidebar .nav-link').forEach(function (link) {
    link.addEventListener('click', function () {
      if (window.innerWidth < 768) closeSidebar();
    });
  });
})();

/* ─── Auto-dismiss alerts ────────────────────────────── */
(function () {
  document.querySelectorAll('.alert-fixed').forEach(function (alert) {
    setTimeout(function () {
      if (alert && document.body.contains(alert)) {
        var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        bsAlert && bsAlert.close();
      }
    }, 5000);
  });
})();

/* ─── Confirmación de eliminación con doble click ───── */
(function () {
  document.querySelectorAll('a[href*="eliminar"]').forEach(function (btn) {
    // Solo enlaces directos que no sean botones de tabla con modal
    if (btn.classList.contains('btn-outline-danger') && !btn.closest('form')) {
      // No interferir con el confirmar_eliminar.html — solo tablas
    }
  });
})();

/* ─── Tour guiado con Driver.js ──────────────────────── */
function reiniciarTour() {
  // Driver.js v1.x expone window.driver.js.driver
  const driverFn = (window.driver && window.driver.js && window.driver.js.driver)
    || (typeof driver !== 'undefined' ? driver : null);
  if (!driverFn) { console.warn('Driver.js no disponible'); return; }

  const tour = driverFn({
    showProgress: true,
    animate: true,
    smoothScroll: true,
    allowClose: true,
    overlayColor: 'rgba(0,0,0,0.6)',
    popoverClass: 'driver-popover',
    steps: [
      {
        element: '#nav-dashboard',
        popover: {
          title: '📊 Dashboard',
          description: 'Tu centro de mando. Aquí ves las métricas más importantes: vacantes abiertas, candidatos en proceso, Time-to-Hire promedio y próximas entrevistas.',
          side: 'right', align: 'start'
        }
      },
      {
        element: '#nav-reclutadores',
        popover: {
          title: '👥 Reclutadores',
          description: 'Gestiona el equipo de RRHH. Cada vacante debe tener un reclutador responsable asignado.',
          side: 'right', align: 'start'
        }
      },
      {
        element: '#nav-vacantes',
        popover: {
          title: '💼 Vacantes',
          description: 'Crea y administra las posiciones abiertas. Define departamento, modalidad, salario y fecha de cierre.',
          side: 'right', align: 'start'
        }
      },
      {
        element: '#nav-candidatos',
        popover: {
          title: '🙋 Candidatos',
          description: 'Registra postulantes, sube su hoja de vida en PDF y da seguimiento a cada etapa del proceso.',
          side: 'right', align: 'start'
        }
      },
      {
        element: '#nav-entrevistas',
        popover: {
          title: '🗓️ Entrevistas',
          description: 'Programa entrevistas presenciales, virtuales o telefónicas. Coordina agendas sin conflictos.',
          side: 'right', align: 'start'
        }
      },
      {
        element: '#nav-evaluaciones',
        popover: {
          title: '⭐ Evaluaciones',
          description: 'Califica candidatos del 1 al 5 y define tu recomendación. Usa los atajos de teclado 1-5 para calificar rápido.',
          side: 'right', align: 'start'
        }
      },
      {
        element: '#nav-pipeline',
        popover: {
          title: '🗂️ Pipeline Kanban',
          description: 'Visualiza todos los candidatos por etapa. Arrastra y suelta las tarjetas para mover candidatos entre fases del proceso.',
          side: 'right', align: 'start'
        }
      },
      {
        element: '#nav-calendario',
        popover: {
          title: '📅 Calendario',
          description: 'Vista de calendario con FullCalendar. Haz clic en cualquier fecha para programar una entrevista directamente.',
          side: 'right', align: 'start'
        }
      },
      {
        element: '#nav-reportes',
        popover: {
          title: '📈 Reportes',
          description: 'Analiza la efectividad de fuentes de reclutamiento (LinkedIn, Portal Web, Referidos) y el Time-to-Hire promedio.',
          side: 'right', align: 'start'
        }
      },
      {
        element: '#nav-perfil',
        popover: {
          title: '👤 Mi Perfil',
          description: 'Actualiza tus datos personales y cambia tu contraseña cuando necesites.',
          side: 'right', align: 'start'
        }
      },
      {
        popover: {
          title: '🎉 ¡Bienvenido al Sistema ATS!',
          description: '<strong>Política de contratación inclusiva:</strong> Nuestro proceso garantiza igualdad de oportunidades para todos los candidatos, evaluación objetiva basada en competencias y transparencia en cada etapa del proceso de selección.',
        }
      }
    ]
  });

  tour.drive();
}

/* ─── Iniciar tour automático en primer acceso ────────── */
(function () {
  if (!localStorage.getItem('ats_tour_done')) {
    // Pequeño delay para que cargue la UI
    setTimeout(function () {
      try { reiniciarTour(); } catch (e) {}
    }, 1200);
    localStorage.setItem('ats_tour_done', '1');
  }
})();

/* ─── Validación visual en tiempo real ──────────────── */
(function () {
  // Marcar campo como válido al escribir
  document.querySelectorAll('.form-control, .form-select').forEach(function (el) {
    el.addEventListener('input', function () {
      if (this.value.trim()) {
        this.classList.remove('is-invalid');
      }
    });
    el.addEventListener('blur', function () {
      if (this.required && !this.value.trim()) {
        this.classList.add('is-invalid');
      }
    });
  });
})();

/* ─── Confirmación con tooltip antes de eliminar ─────── */
(function () {
  // Inicializar tooltips de Bootstrap en todos los elementos con title
  var tooltipTriggerList = document.querySelectorAll('[title]');
  tooltipTriggerList.forEach(function (el) {
    if (!el.getAttribute('data-bs-toggle')) {
      el.setAttribute('data-bs-toggle', 'tooltip');
      new bootstrap.Tooltip(el, { trigger: 'hover', placement: 'top' });
    }
  });
})();

/* ─── Búsqueda con Enter ─────────────────────────────── */
(function () {
  document.querySelectorAll('input[name="q"]').forEach(function (input) {
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.closest('form') && this.closest('form').submit();
      }
    });
  });
})();
