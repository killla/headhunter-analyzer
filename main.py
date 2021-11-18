from time import sleep

import requests
from environs import Env
from terminaltables import AsciiTable

LANGS = ['JavaScript',
         'Java',
         'Python',
         'Ruby',
         'PHP',
         'C++',
         'C#',
         'Go',
         'Scala',
         'TypeScript']

CITIES = {'Moscow': {'area_id': 1,
                     'town_id': 4}}


def predict_salary(salary_from, salary_to):
    match salary_from, salary_to:
        case 0 | None, 0 | None:
            return
        case 0 | None, salary:
            return salary*0.8
        case salary, 0 | None:
            return salary*1.2
        case _:
            return (salary_from + salary_to) // 2


def predict_rub_salary_hh(vacancy):
    if vacancy['salary']['currency'] == 'RUR':
        return predict_salary(vacancy['salary']['from'], vacancy['salary']['to'])


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def get_vacancies_count_hh(text, city):
    url = 'https://api.hh.ru/vacancies'
    headers = {'User-Agent': 'HH-User-Agent'}
    payload = {'area': city,
               'professional_role': 96,
               'period': 30,
               'text': text, }
    response = requests.get(url, params=payload, headers=headers)

    return response.json()['found']


def get_average_salary_hh(text, city):
    vacancies_processed, salary_sum = 0, 0
    page, pages = 0, 1
    url = 'https://api.hh.ru/vacancies'
    headers = {'User-Agent': 'HH-User-Agent'}
    payload = {'area': city,
               'professional_role': 96,
               'period': 30,
               'only_with_salary': True,
               'per_page': 100,
               'text': text, }

    while page < pages:
        payload['page'] = page
        response = requests.get(url, params=payload, headers=headers)
        vacancies = response.json()['items']
        for vacancy in vacancies:
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                vacancies_processed += 1
                salary_sum += salary
        pages = response.json()['pages']
        page += 1

    average_salary = salary_sum // vacancies_processed
    return int(average_salary), vacancies_processed


def get_vacancies_count_sj(text, town, secret_key):
    url = 'https://api.superjob.ru/2.2/vacancies'
    headers = {'X-Api-App-Id': secret_key}
    payload = {'town': town,
               'catalogues': 48,
               'keyword': text}
    response = requests.get(url, params=payload, headers=headers)
    return response.json()['total']


def get_average_salary_sj(text, town, secret_key):
    vacancies_processed, salary_sum, page = 0, 0, 0
    count_per_page = 100
    url = 'https://api.superjob.ru/2.2/vacancies'
    headers = {'X-Api-App-Id': secret_key}
    payload = {'town': town,
               'catalogues': 48,
               'count': count_per_page,
               'no_agreement': 1,
               'keyword': text}
    more = True
    while more:
        payload['page'] = page
        response = requests.get(url, params=payload, headers=headers)
        vacancies = response.json()['objects']
        for vacancy in vacancies:
            salary = predict_rub_salary_sj(vacancy)
            if salary:
                vacancies_processed += 1
                salary_sum += salary
        more = response.json()['more']
        page += 1
    average_salary = salary_sum // vacancies_processed
    return int(average_salary), vacancies_processed


def print_table(langs_data, title):
    table_data = [
        ['Язык программирования', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата, ₽']
    ]
    for lang, lang_data in langs_data.items():
        table_line = [lang, *lang_data.values()]
        table_data.append(table_line)

    table_instance = AsciiTable(table_data, title)
    print(table_instance.table)
    print()


if __name__ == '__main__':
    city = 'Moscow'
    result = {}
    for lang in LANGS:
        vacancies_found = get_vacancies_count_hh(lang, CITIES[city]['area_id'])
        average_salary, vacancies_processed = get_average_salary_hh(lang, CITIES[city]['area_id'])
        result[lang] = {'vacancies_found': vacancies_found,
                        'vacancies_processed': vacancies_processed,
                        'average_salary': average_salary}
    title = f'HeadHunter {city}'
    print_table(result, title)

    env = Env()
    env.read_env()
    secret_key = env.str('SUPERJOB_SECRET_KEY')

    result = {}
    for lang in LANGS:
        vacancies_found = get_vacancies_count_sj(lang, CITIES[city]['town_id'], secret_key)
        average_salary, vacancies_processed = get_average_salary_sj(lang, CITIES[city]['town_id'], secret_key)
        result[lang] = {'vacancies_found': vacancies_found,
                        'vacancies_processed': vacancies_processed,
                        'average_salary': average_salary}
    title = f'SuperJob {city}'
    print_table(result, title)
