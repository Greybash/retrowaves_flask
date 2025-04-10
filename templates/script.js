window.addEventListener('scroll', function() {
    if (window.scrollY > 50) {
        document.body.classList.add('scrolled');
    } else {
        document.body.classList.remove('scrolled');
    }
    const stars = document.querySelectorAll('.star');
    stars.forEach(star => {
        star.style.animation = 'star-move 2s infinite alternate';
    });
});

document.getElementById('modeToggle').addEventListener('click', function() {
    document.body.classList.toggle('light-mode');
    const icon = this.querySelector('i');
    if (document.body.classList.contains('light-mode')) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    }
});

function addStars() {
    for (let i = 0; i < 100; i++) {
        const star = document.createElement('div');
        star.classList.add('star');
        const sizeClass = ['small', 'medium', 'large'][Math.floor(Math.random() * 3)];
        star.classList.add(sizeClass);
        star.style.top = `${Math.random() * 100}vh`;
        star.style.left = `${Math.random() * 100}vw`;
        document.body.appendChild(star);
    }
}

addStars();