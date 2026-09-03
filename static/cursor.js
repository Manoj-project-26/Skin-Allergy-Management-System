// ⭐ Star Cursor Animation

document.addEventListener("mousemove", function (event) {

    const star = document.createElement("span");

    star.innerHTML = "✦";

    star.style.position = "fixed";
    star.style.left = event.clientX + "px";
    star.style.top = event.clientY + "px";

    star.style.color = "#d4af37";
    star.style.fontSize = (Math.random() * 10 + 10) + "px";
    star.style.pointerEvents = "none";
    star.style.zIndex = "99999";

    star.style.transform = "translate(-50%, -50%)";
    star.style.transition =
        "transform 0.8s ease-out, opacity 0.8s ease-out";

    document.body.appendChild(star);

    setTimeout(function () {
        star.style.transform =
            "translate(-50%, -50%) scale(0) rotate(180deg)";
        star.style.opacity = "0";
    }, 50);

    setTimeout(function () {
        star.remove();
    }, 850);
});