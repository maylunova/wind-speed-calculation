# Андрей Аракельянц. 23.01.2018
# Задача этой программы - по данным наблюдений с сайта rp5.ru рассчитать
# скорость ветра заданной обеспеченности по каждому румбу.

from pandas import *
import io

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy
from constants import (
    WIND_SPEED, WIND_DIRECTION, CALM, ALL,
    STORM_DURATION, COEF, MINIMAL_TICK,
    MAXIMAL_TICK, TICKS_NUMBER, MINIMAL_X, MINIMAL_Y, MAXIMAL_Y, PER_CENT
)
from datetime import date, timedelta


# Из набора данных создаю сводную таблицу
def get_pivot_table(data):
    # создаю таблицу с данными о скорости и направлении ветра
    direction = []
    speed = []
    for observation in data:
        direction.append(observation.wind_direction)
        speed.append(observation.wind_speed)
    observation_data = {WIND_SPEED: speed, WIND_DIRECTION: direction}
    required_data = pandas.DataFrame(data=observation_data)
    # добавляю вспомогательный столбец, который нужен для создания сводной
    # таблицы
    required_data = required_data.assign(Wind_speed_dublicate=required_data[WIND_SPEED])
    # создаю сводную таблицу с количеством наблюдений по каждому сочетанию
    # скорости-направления ветра (в дальнейшем называю это сочетание словом
    # "градация"). Строки таблицы - скорость ветра. Столбцы таблицы - направление ветра.
    velocity_direction_table = pandas.pivot_table(
        required_data, index=WIND_SPEED, values='Wind_speed_dublicate', columns=WIND_DIRECTION,
        margins=True, aggfunc=numpy.size
    )
    # во всех ячейках без значений ставлю нули
    velocity_direction_table = velocity_direction_table.fillna(value=0)
    return velocity_direction_table


# Обрабатываю случаи штилей
def process_calm_cases(velocity_direction_table):
    # Нужно распределить штили равномерно по всем направлениями ветра.
    # количество колонок в таблице
    column_number = len(velocity_direction_table.columns)
    # количество штилей
    calm_cases = velocity_direction_table.loc[0, CALM]
    # Вычисляю количество штилей, равномерно распределённое по всем направлениями ветра.
    # Для этого делю общее количество штилей на количество наблюдённых направлений ветра.
    #  Вычитаю 2 из общего числа колонок, так как две правые колонки - это "All" и "Штиль, безветрие"
    calm_cases_per_each_direction = calm_cases / (column_number - 2)
    return calm_cases_per_each_direction


def get_table_2(velocity_direction_table):
    # делаю таблицу с повторяемостью градаций в каждом румбе в процентах (таблица 3.2)
    for column in velocity_direction_table.columns:
        cases_with_this_direction = velocity_direction_table.loc[ALL, column]
        velocity_direction_table[column] = velocity_direction_table[column] / cases_with_this_direction
    # удаляю столбец "All", потому что он не нужен
    velocity_direction_table = velocity_direction_table.drop(columns=ALL)
    velocity_direction_table = velocity_direction_table * PER_CENT
    return velocity_direction_table


# делаю таблицу с продолжительностью каждой градации по каждому
# направлению (таблица 3.3)
def get_table_3(velocity_direction_table):
    # добавить исключение
    # рассчитываю количество строк в таблице
    row_number = len(velocity_direction_table.iloc[:, 1])
    # обнуляю самую нижнюю строку таблицы
    # TODO fix scenario with row_number = 0
    velocity_direction_table.iloc[row_number - 1] = 0
    # TODO fix scenario with row_number = 0
    row_index = row_number - 2
    # делаю таблицу с продолжительностью каждой градации по каждому
    # направлению (таблица 3.3)
    while row_index != -1:
        velocity_direction_table.iloc[row_index] += velocity_direction_table.iloc[row_index + 1]
        row_index -= 1
    # заменяю название строки All на значение скорости ветра, который не
    # наблюдался
    max_observed_wind_velocity = velocity_direction_table.index[row_number - 2]
    # TODO variable with _2 in name is BAD, maybe you can just
    # TODO velocity_direction_table.rename({'All': (max_observed_wind_velocity + 1)}, axis='index')
    velocity_direction_table_2 = velocity_direction_table.rename(
        {ALL: (max_observed_wind_velocity + 1)}, axis='index')
    return velocity_direction_table_2


# вычисляю скорость ветра по значению режимной функции
def get_wind_speed(f_big, velocity_direction_table, column_number):
    row_number = 0

    for duration in velocity_direction_table.iloc[:, column_number]:
        if f_big < duration:
            row_number += 1
            continue

        if f_big == duration:
            return velocity_direction_table.index[row_number]

        lower_wind_speed = velocity_direction_table.index[row_number - 1]
        bigger_wind_speed = velocity_direction_table.index[row_number]
        lower_duration = velocity_direction_table.iloc[
            row_number - 1, column_number]
        durations = numpy.array([lower_duration, duration])
        speeds = numpy.array([lower_wind_speed, bigger_wind_speed])
        # вычисляю нужную нам скорость ветра, линейно интерполируя между
        # строками таблицы 3.3
        return numpy.interp(f_big, durations, speeds)


# вычисляем значение режимной функции F по формуле (3.1) и рассчитываю
# скорость ветра
def calculate_speed(direction_recurrence, velocity_direction_table, storm_recurrence, start_date, end_date):
    start_date = datetime.strptime(start_date, '%d.%m.%Y')
    end_date = datetime.strptime(end_date, '%d.%m.%Y')
    # выбрал 2016 год, потому что он високосный и ему подойдёт любая дата
    start_date_without_year = start_date.replace(year=2016)
    end_date_without_year = end_date.replace(year=2016)
    time_difference = end_date_without_year - start_date_without_year
    days_number = 365
    if time_difference.days > 0:
        days_number = time_difference.days
    # рассчитываем F для каждого направления ветра
    column_number = 0
    wind_speed_dict = {}
    # перебираю каждый столбец таблицы 3.3, то есть каждое направление ветра
    for direction_recurrence in direction_recurrence.loc['All']:
        # рассчитываю значение режимной функции по формуле 3.1
        f_big = COEF * STORM_DURATION / (
                days_number * storm_recurrence * direction_recurrence)
        # вычисляю скорость ветра по значению режимной функции, линейно
        # интерполируя между строками таблицы 3.3
        wind_speed = get_wind_speed(f_big, velocity_direction_table, column_number)
        wind_speed_dict.update({velocity_direction_table.columns[column_number]: wind_speed})
        column_number += 1
    return wind_speed_dict


# создаю график режимных скоростей ветра
def get_picture(velocity_direction_table):
    # TODO подписать оси на рисунке, добавить легенду
    velocity_axis = velocity_direction_table.index.values
    figure = plt.figure()
    # создаю две пары осей: слева и справа
    left_graphs = figure.add_subplot(1, 2, 1)
    right_graphs = figure.add_subplot(1, 2, 2)
    graph_number = 0
    for direction in velocity_direction_table.columns:
        graph_number += 1
        duration_axis = velocity_direction_table[direction].values
        # рисую график на левых осях. Если графиков на левых осях становится
        # больше 8, то рисую графики на правых осях
        if graph_number <= 8:
            left_graphs.plot(velocity_axis, duration_axis, label=graph_number)
        else:
            right_graphs.plot(velocity_axis, duration_axis, label=graph_number)
    y_labels = numpy.geomspace(MINIMAL_TICK, MAXIMAL_TICK, TICKS_NUMBER)
    maximal_x = velocity_axis.max()
    for picture in [left_graphs, right_graphs]:
        # делаю вертикальную ось логарифмической c симметрией относительно 0,
        # при значениях ниже 5 рисуется прямая линия
        picture.set_yscale('symlog', linthreshy=5)
        picture.set_yticks(y_labels)
        picture.yaxis.set_major_formatter(ticker.ScalarFormatter())
        picture.axis([MINIMAL_X, maximal_x, MAXIMAL_Y, MINIMAL_Y])
        picture.legend()

    # немного увеличиваю расстояние между левым и правым рисунком
    plt.tight_layout(w_pad=1)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=400)
    plt.savefig('picture.png', format='png', dpi=400)
    buf.seek(0)
    return buf


def get_calculation_results(data, storm_recurrence, start_date, end_date):
    velocity_direction_table = get_pivot_table(data)
    observations_number = velocity_direction_table.loc[ALL, ALL]
    # обрабатываю штили
    column_names = []
    for column in velocity_direction_table.columns:
        column_names.append(column)
    if column_names.count(CALM) > 0:
        calm_cases_per_each_direction = process_calm_cases(velocity_direction_table)
        # записываю в каждый столбец строчки "0" количество штилей, распределённое
        # по направлениям
        velocity_direction_table.loc[0] = calm_cases_per_each_direction
        # прибавляю в строку "All" количество штилей, распределённое по направлениям
        velocity_direction_table.loc[ALL] = velocity_direction_table.loc[ALL] + calm_cases_per_each_direction
        velocity_direction_table = velocity_direction_table.drop(columns=CALM)
    # делаю таблицу с повторяемостью градаций от общего числа всех наблюдений
    # (таблица 3.1)
    direction_recurrence = velocity_direction_table / observations_number
    direction_recurrence = direction_recurrence.drop(columns=ALL)
    # делаю таблицу с повторяемостью градаций в каждом румбе в процентах (таблица 3.2)
    velocity_direction_table = get_table_2(velocity_direction_table)
    # делаю таблицу с продолжительностью каждой градации по каждому
    # направлению (таблица 3.3)
    velocity_direction_table = get_table_3(velocity_direction_table)
    # эта таблица содержит координаты режимных функций ветра (рисунок 1)
    # делаю рисунок режимных функций ветра по каждому направлению (рисунок 1)
    image_buf = get_picture(velocity_direction_table)
    # рассчитываю значение режимной функции для каждого направления ветра
    calculated_wind_speed = calculate_speed(direction_recurrence, velocity_direction_table,
                                            storm_recurrence, start_date, end_date
    )
    print(calculated_wind_speed)
    return velocity_direction_table, calculated_wind_speed, image_buf


if __name__ == '__main__':
    get_calculation_results()
