const canvas = document.querySelector("#board-canvas");
const context = canvas.getContext("2d");

context.fillStyle = "#fffaf0";
context.fillRect(0, 0, canvas.width, canvas.height);
context.strokeStyle = "#2f2f2f";
context.lineWidth = 8;
context.strokeRect(4, 4, canvas.width - 8, canvas.height - 8);
