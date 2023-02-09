btn = document.querySelector('.return-btn')
btn.addEventListener('focus', (e) => {
    e.target.classList.add('return-btn-modifier');
    setTimeout(() => {
        e.target.classList.remove('return-btn-modifier');
    }, 1000)
})