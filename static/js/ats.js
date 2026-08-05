/**
 * ATS - Sistema de Reclutamiento
 * JavaScript principal: utilidades generales, mensajes y tour guiado (Driver.js)
 */

/* ─── Auto-ocultar alertas después de 5 segundos ─── */
document.addEventListener('DOMContentLoaded', function () {
  const alertas = document.querySelectorAll('.alert-fixed');
  alertas.forEach(function (alerta) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alerta);
      bsAlert.close();
    }, 5000);
  });

  /* ─── Confirmación de eliminación ─── */
  document.querySelectorAll('[data-confirm]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm || '¿Estás seguro de eliminar este registro?')) {
        e.preventDefault();
      }
    });
  });

  /* ─── Toggle sidebar en móvil ─── */
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });
  }

  /* ─── Iniciar tour guiado si es la primera visita ─── */
  if (typeof driver !== 'undefined' && !localStorage.getItem('tour_completado')) {
    iniciarTourDashboard();
  }
});

/* ─────────────────────────────────────────────
   TOUR GUIADO — Driver.js
   Política de contratación inclusiva
───────────────────────────────────────────── */
function iniciarTourDashboard() {
  const driverObj = driver({
    showProgress: true,
    progressText: 'Paso {{current}} de {{total}}',
    nextBtnText: 'Siguiente →',
    prevBtnText: '← Anterior',
    doneBtnText: '¡Entendido!',
    onDestroyStarted: () => {
      localStorage.setItem('tour_completado', '1');
      driverObj.destroy();
    },
    steps: [
      {
        element: '#sidebar',
        popover: {
          title: '🏢 Sistema ATS',
          description: 'Bienvenido al Sistema de Reclutamiento. Este menú te da acceso a todas las funcionalidades: Dashboard, Candidatos, Entrevistas, Pipeline y más.',
          side: 'right',
        }
      },
      {
        element: '#nav-dashboard',
        popover: {
          title: '📊 Dashboard',
          description: 'Aquí puedes ver las métricas principales: vacantes abiertas, candidatos en proceso, tiempo promedio de contratación (Time-to-Hire) y contrataciones por mes.',
          side: 'right',
        }
      },
      {
        element: '#nav-vacantes',
        popover: {
          title: '📋 Vacantes',
          description: 'Gestiona las posiciones disponibles. Puedes crear, editar y cerrar vacantes, indicando departamento, modalidad y salario.',
          side: 'right',
        }
      },
      {
        element: '#nav-candidatos',
        popover: {
          title: '👥 Candidatos',
          description: 'Registra y gestiona a todos los postulantes. Puedes adjuntar la hoja de vida en PDF y hacer seguimiento de su etapa en el proceso.',
          side: 'right',
        }
      },
      {
        element: '#nav-pipeline',
        popover: {
          title: '🔄 Pipeline de Selección',
          description: 'Vista Kanban donde puedes arrastrar candidatos entre las etapas: Postulado → Preselección → Entrevista → Evaluación → Oferta → Contratado.',
          side: 'right',
        }
      },
      {
        element: '#nav-calendario',
        popover: {
          title: '📅 Calendario de Entrevistas',
          description: 'Agenda y gestiona entrevistas directamente en el calendario. Puedes verlas por día, semana o mes y crear nuevas haciendo clic en una fecha.',
          side: 'right',
        }
      },
      {
        element: '#nav-reportes',
        popover: {
          title: '📈 Reportes',
          description: 'Analiza la efectividad del proceso de reclutamiento. Ve el tiempo promedio de contratación y la efectividad de fuentes como LinkedIn, Portal Web y Referidos.',
          side: 'right',
        }
      },
      {
        popover: {
          title: '🤝 Política de Contratación Inclusiva',
          description: '<strong>Nuestro compromiso:</strong><br>' +
            '✅ Evaluamos candidatos por sus habilidades y potencial, sin discriminación por género, edad, origen étnico, discapacidad, orientación sexual o condición socioeconómica.<br><br>' +
            '✅ Todas las entrevistas siguen una estructura estandarizada con criterios objetivos y medibles.<br><br>' +
            '✅ Promovemos activamente la diversidad en todos los niveles de la organización.<br><br>' +
            '✅ Los datos del sistema son confidenciales y se usan exclusivamente para el proceso de selección.',
        }
      },
    ]
  });
  driverObj.drive();
}

/* ─── Botón para reiniciar el tour ─── */
function reiniciarTour() {
  localStorage.removeItem('tour_completado');
  iniciarTourDashboard();
}
