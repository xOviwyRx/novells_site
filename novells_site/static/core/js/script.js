
function ajaxSend(url, params) {
    // Отправляем запрос
    fetch(`${url}?${params}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    })
        .then(response => response.json())
        .then(json => render(json))
        .catch(error => console.error(error))
}

// Filter movies
// const forms = document.querySelector('form[name=filter]');
//
// forms.addEventListener('submit', function (e) {
//     // Получаем данные из формы
//     e.preventDefault();
//     let url = this.action;
//     let params = new URLSearchParams(new FormData(this)).toString();
//     ajaxSend(url, params);
// });

function render(data) {
    // Рендер шаблона
    let template = Hogan.compile(html);
    let output = template.render(data);

    const div = document.querySelector('.marat>.row');
    div.innerHTML = output;
}

let html = '\
{{#novells}}\
<div class="card d-flex col border-0 mt-1">\
    <div class="card-img-top">\
        <a href="{{ slug }}">\
        <img src="media/{{ poster }}" class="card-img-top rounded"\
                                             alt="{{ original_title }}">\
                                    </a>\
                                </div>\
                                <div class="card-body">\
                                    <h6 class="card-title mt-1">\
                                        <div class="pb-2">\
                                            <span class="bi bi-star-fill checked align-bottom"></span>\
                                            <span class="bi bi-star-fill checked"></span>\
                                            <span class="bi bi-star-fill checked"></span>\
                                            <span class="bi bi-star-half checked"></span>\
                                            <span class="bi bi-star checked"></span>\
                                            <span class="align-bottom">5</span>\
                                        </div>\
                                    </h6>\
                                    <h6 class="card-subtitle"><a\
                                            href="{{ slug }}">{{ slug }}</a>\
                                    </h6>\
                                </div>\
                           </div>\
{{/novells}}'