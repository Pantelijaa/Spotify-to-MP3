loginBtn = document.querySelector('.login-btn');
loginBtn.addEventListener('focus', (e) => {
    console.log(e)
    e.target.classList.add('login-btn-modifier'); 
    setTimeout(() => {
        e.target.classList.remove('login-btn-modifier');
    }, 1000)
})