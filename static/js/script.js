// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // Selecciona el botón por su ID
    const myButton = document.getElementById('myButton');
    // Selecciona el área donde se mostrará el mensaje
    const messageArea = document.getElementById('messageArea');

    // Agrega un "escuchador de eventos" al botón
    if (myButton) {
        myButton.addEventListener('click', function() {
            // Cuando se hace clic, cambia el texto del área de mensaje
            messageArea.textContent = '¡Has hecho clic en el botón!';
            messageArea.style.color = '#e74c3c'; // Cambia el color del texto
        });
    } else {
        console.error('El botón con ID "myButton" no fue encontrado.');
    }
});