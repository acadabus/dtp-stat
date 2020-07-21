from django.core.management.base import BaseCommand

from application import utils
from data import utils as data_utils
from data.models import Region

coords = {
    "Щигровский район": "36.805181 51.901798",
    "Черемисиновский район": "37.202362 51.907299",
    "Хомутовский район": "34.670532 51.872275",
    "Фатежский район": "35.848206 52.082869",
    "Тимский район": "37.122484 51.675164",
    "Суджанский район": "35.287414 51.23318",
    "Воронеж": "39.200269 51.660781",
    "Солнцевский район": "36.735768 51.469878",
    "Совесткий район": "63.364762 60.892832",
    "Судиславский район": "41.708141 57.891468",
    "Эртильский район": "40.72789 51.759944",
    "Хохольский район": "38.896055 51.433664",
    "Рыльский район": "34.583153 51.593448",
    "Сусанинский район": "41.555571 58.148154",
    "Островский район": "28.610965 57.231751",
    "Унеченский район": "32.805486 52.835563",
    "Юрьевецкий район": "42.955595 57.251135",
    "Терновский район": "41.508338 51.638361",
    "Таловский район": "40.756834 51.168176",
    "Пристенский район": "36.562321 51.214994",
    "Чухломский район": "42.998607 58.897709",
    "Солигаличский район": "42.198855 59.052572",
    "Трубчевский район": "33.803829 52.600863",
    "Суражский район": "32.453239 53.082975",
    "Южский район": "42.106256 56.555848",
    "Обнинск": "36.597041 55.117092",
    "Юринский район": "46.073064 56.552087",
    "Семилукский район": "38.720865 51.823944",
    "Россошанский район": "39.694369 50.174972",
    "Юрьев-Полский район": "39.703865 56.535185",
    "Белгород": "36.587268 50.595414",
    "Янаульский": "54.907186 56.235385",
    "Суземский район": "34.122722 52.336424",
    "Стародубский район": "32.720137 52.480179",
    "Шаройский район": "45.781578 42.597943",
    "Шпаковский район": "42.15561 44.921259",
    "Владикавказ": "44.681762 43.024616",
    "Савинский район": "41.298572 56.579147",
    "Родниковский район": "41.724481 57.085775",
    "Калуга": "36.261215 54.513845",
    "Юхновский район": "35.259171 54.715421",
    "Советский район": "63.364762 60.892832",
    "Репьевский район": "38.704085 51.154433",
    "Селивановский район": "41.647918 55.826306",
    "Петушинский район": "39.42068 55.965043",
    "Октябрьский район": "131.549362 44.086078",
    "Обоянский район": "36.145449 51.23358",
    "Антроповский район": "43.004347 58.287458",
    "Нальчик": "43.607072 43.485259",
    "Яковлевский район": "133.543263 44.433721",
}


class Command(BaseCommand):
    help = "Debug get region"

    def handle(self, *args, **options):
        # self.collect_coords()

        matched = 0
        for k, v in coords.items():
           result = utils.get_region_by_center_point(v)
           print(result)
           if result and result.name == k:
               # print('MATCH')
               matched += 1
           else:
               print('MISMATCH %s %s %s' % (k, v, result))

        print('matched %s from %s regions' % (matched, len(coords.keys())))

    def collect_coords(self):
        coords = {}
        for region in Region.objects.filter(level=2).all()[30:50]:
            result = data_utils.geocoder_yandex(region.name)
            coords[region.name] = "%s %s" % (result["long"], result["lat"])

        print(coords)
