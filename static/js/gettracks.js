downloadBtn = document.querySelectorAll('.download-btn');
downloadBtn.forEach(btn => {
    btn.addEventListener('focus', (e) => {
        e.target.classList.add('download-btn-modifier');
        setTimeout(() => {
            e.target.classList.remove('download-btn-modifier');
        }, 1000)
    })
})
