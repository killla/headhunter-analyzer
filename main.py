import requests
from environs import Env
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) // 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    if vacancy['salary']['currency'] == 'RUR':
        return predict_salary(vacancy['salary']['from'], vacancy['salary']['to'])


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def get_average_salary_hh(text, city, profession=96):
    """
    return only vacancies with salary, not all vacancies
    """
    vacancies_processed, salary_sum = 0, 0
    page, pages = 0, 1
    url = 'https://api.hh.ru/vacancies'
    headers = {'User-Agent': 'HH-User-Agent'}
    payload = {'area': city,
               'professional_role': profession,
               'period': 30,
               'only_with_salary': True,
               'per_page': 100,
               'text': text, }

    while page < pages:
        payload['page'] = page
        response = requests.get(url, params=payload, headers=headers)
        response.raise_for_status()
        response = response.json()
        for vacancy in response['items']:
            if salary := predict_rub_salary_hh(vacancy):
                vacancies_processed += 1
                salary_sum += salary
        pages = response['pages']
        page += 1
    vacancies_found = response['found']
    average_salary = salary_sum // vacancies_processed
    return vacancies_found, vacancies_processed, average_salary


def get_average_salary_sj(text, town, secret_key, profession=48):
    """
    return only vacancies with salary, not all vacancies
    """
    vacancies_processed, salary_sum, page = 0, 0, 0
    count_per_page = 100
    url = 'https://api.superjob.ru/2.2/vacancies'
    headers = {'X-Api-App-Id': secret_key}
    payload = {'town': town,
               'catalogues': profession,
               'count': count_per_page,
               'no_agreement': 1,
               'keyword': text}
    more = True
    while more:
        payload['page'] = page
        response = requests.get(url, params=payload, headers=headers)
        response.raise_for_status()
        response = response.json()
        for vacancy in response['objects']:
            if salary := predict_rub_salary_sj(vacancy):
                vacancies_processed += 1
                salary_sum += salary
        more = response['more']
        page += 1
    vacancies_found = response['total']
    average_salary = salary_sum // vacancies_processed
    return vacancies_found, vacancies_processed, average_salary


def get_table(langs_data, title):
    table_data = [
        ['Язык программирования', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата, ₽']
    ]
    for lang, lang_data in langs_data.items():
        table_line = [lang, *lang_data.values()]
        table_data.append(table_line)

    table_instance = AsciiTable(table_data, title)
    return table_instance.table


if __name__ == '__main__':
    langs = ['JavaScript',
             'Java',
             'Python',
             'Ruby',
             'PHP',
             'C++',
             'C#',
             'Go',
             'Scala',
             'TypeScript']

    city, area_id, town_id = 'Moscow', 1, 4
    hh_salaries = {}
    for lang in langs:
        vacancies_found, vacancies_processed, average_salary = \
            get_average_salary_hh(lang, area_id)
        hh_salaries[lang] = {'vacancies_found': vacancies_found,
                        'vacancies_processed': vacancies_processed,
                        'average_salary': average_salary}
    print(get_table(hh_salaries, f'HeadHunter {city}'))
    print()

    env = Env()
    env.read_env()
    secret_key = env.str('SUPERJOB_SECRET_KEY')

    sj_salaries = {}
    for lang in langs:
        vacancies_found, vacancies_processed, average_salary = \
            get_average_salary_sj(lang, town_id, secret_key)
        sj_salaries[lang] = {'vacancies_found': vacancies_found,
                        'vacancies_processed': vacancies_processed,
                        'average_salary': average_salary}
    print(get_table(sj_salaries, f'SuperJob {city}'))
