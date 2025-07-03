// Protección básica de código frontend
// Dificulta la inspección y copia, pero no lo impide totalmente

document.addEventListener('contextmenu', function(e) {
  e.preventDefault();
});
document.addEventListener('keydown', function(e) {
  // F12, Ctrl+Shift+I, Ctrl+U, Ctrl+S, Ctrl+Shift+C
  if (
    e.key === 'F12' ||
    (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'C')) ||
    (e.ctrlKey && (e.key === 'U' || e.key === 'S'))
  ) {
    e.preventDefault();
    return false;
  }
});
// Opcional: Oculta el texto de copyright en el código fuente
// (No recomendado para accesibilidad, pero posible)
