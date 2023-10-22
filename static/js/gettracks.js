downloadBtn = document.querySelectorAll('.download-btn');
downloadBtn.forEach(btn => {
    btn.addEventListener('focus', (e) => {
        e.target.classList.add('download-btn-modifier');
        setTimeout(() => {
            e.target.classList.remove('download-btn-modifier');
        }, 1000)
    })
})

profile = document.querySelector('#profile');
dropmenu = document.querySelector('#drop-menu')
arrow = document.querySelector('#dropdown .material-symbols-outlined')
profile.addEventListener('click', e => {
    if (arrow.innerText === 'arrow_drop_down'){
        dropmenu.classList.add('disp-block');
        profile.style.backgroundColor = 'var(--drop-down-color)';
        arrow.innerText = 'arrow_drop_up';
    } else {
        dropmenu.classList.remove('disp-block');
        profile.style.backgroundColor = 'black';
        arrow.innerText = 'arrow_drop_down';
    }
})

$(function() {
    $('a#logout-btn').on('click', e => {
        e.preventDefault()
        $.getJSON('/force_logout',
            function(data) {
                location.reload()
            });
            return false;
    });
});
