![Last Commit](https://img.shields.io/github/last-commit/kdavjd/deconvolution_app)
![Python 3.11](https://img.shields.io/badge/python-3.11.5-blue.svg)
![pyqt](https://img.shields.io/badge/-pyqt-green)
![scipy](https://img.shields.io/badge/-scipy-red)
![pandas](https://img.shields.io/badge/-pandas-blueviolet)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

# deconvolution_app

## Описание

Приложение позволяет произвести деконволюцию DTA термогравиметрического эксперимента и подготовить данные к дальнейшей обработке. Для анализа данных можно использовать другой проект - [isoconversion_study_of_reaction_kinetics](https://github.com/kdavjd/isoconversion_study_of_reaction_kinetics).

### Зависимости

Все необходимые зависимости находятся в файле `requirements.txt`.

### Установка

Для установки приложения запустите `build.bat`, который находится в корне проекта. Это создаст десктопный вариант приложения.

### Использование

## Подготовка данных
Данные должны быть в формате csv, разделитель запятая, столбцы с экспериментальными данными должны называться в формате 'rate_' + скорость нагрева в минутах. Примеры можно посмотреть в папке data:

| temperature | rate_3 | rate_5 | ... | rate_n | 
|:-----------:|:------:|:------:|:---:|:------:|
|  31.63192   |   100  |   100  | ... |   100  |
|  32.58683   |   100  |   100  | ... |   100  |


### Примеры

*Оставим пустым*

## Лицензия

MIT.

## Контакты

Если у вас есть вопросы или предложения по улучшению, пожалуйста, [свяжитесь со мной](https://t.me/nuclearexistence).

