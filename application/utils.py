from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.gis.db.models.functions import Distance
from data import models as data_models
from data import utils as data_utils
from application import models
from django.shortcuts import get_object_or_404, render
from django.db.models import Sum
from django.contrib.gis.measure import D

import json
import calendar
import os
import shutil
from tqdm import tqdm
import pandas as pd


def get_region_by_center_point(center_point):
    region = None
    parent_region_name = None

    if center_point:
        if "," not in center_point:
            # проверяем координаты через Яндекс
            ya_data = data_utils.geocoder_yandex(center_point)
            if ya_data and ya_data.get("address"):
                if "Россия" not in ya_data.get("address") or any(x in ya_data.get("address") for x in [y.name for y in data_models.Region.objects.filter(level=1, is_active=False)]):
                    return None
                if ya_data.get('parent_region'):
                    parent_region_name = ya_data.get('parent_region')

                    if ya_data.get('region') and ya_data.get('region') != ya_data.get('parent_region'):
                        try:
                            region = get_object_or_404(data_models.Region, name=ya_data['region'], parent_region__name=ya_data['parent_region'])
                        except:
                            pass

            # проверяем координаты через ближайшие ДТП
            if not region:
                point = GEOSGeometry('POINT(' + center_point + ')')
                for dist in [0.1, 1, 5, 10, 25, 50, 75, 100]:

                    nearest_dtps = data_models.DTP.objects.all()

                    nearest_dtps = nearest_dtps.filter(
                        point__dwithin=(point, dist)
                    )

                    if nearest_dtps.count() > 4:
                        nearest_dtps = nearest_dtps.annotate(
                            distance=Distance('point', point)
                        )
                        dtps = [x.region.id for x in nearest_dtps.order_by('distance')[0:5]]
                        region_id = max(set(dtps), key=dtps.count)
                        region = get_object_or_404(data_models.Region, id=region_id)
                        break

    return region


def opendata(region=None):
    """
    if region:
        downloads = region.download_set.filter(last_update__isnull=False)

        if downloads:
            latest_update_date=downloads.latest('date').date


        else:
            return
    """

    # get russia dataset
    latest_download = data_models.Download.objects.filter(last_update__isnull=False).latest('date')
    latest_opendata = models.OpenData.objects.filter(region=None).last()

    if latest_opendata and latest_opendata.date == latest_download.date:
        pass
    else:
        data = []
        for obj in tqdm(data_models.DTP.objects.select_related(
                'region', 'category', 'light', 'severity'
        ).prefetch_related(
            'nearby', 'weather', 'tags', 'participant_categories', 'road_conditions'
        ).filter(
            datetime__date__lte=latest_download.date.replace(day=calendar.monthrange(latest_download.date.year, latest_download.date.month)[1])
        ).iterator()):
            data.append(obj.as_dict())

        geo_data = {"type": "FeatureCollection", "features": [
            {"type": "Feature",
             "geometry": {"type": "Point", "coordinates": [item['point']['long'], item['point']['lat']]},
             "properties": item
             } for item in data
        ]}

        file_name = 'russia.geojson'
        path = 'media/opendata/'
        with open(path + file_name, 'w') as data_file:
            json.dump(geo_data, data_file, ensure_ascii=False)

        shutil.make_archive(path + file_name, 'zip', path, file_name)

        latest_opendata, created = models.OpenData.objects.get_or_create(
            region=None
        )
        latest_opendata.date = latest_download.date
        latest_opendata.file_size = os.stat(path + file_name + ".zip").st_size
        latest_opendata.save()

    """
    for region in data_models.Region.objects.filter(level=1, gibdd_code='45'):
        downloads = region.download_set.filter(base_data=True)
        if downloads:
            latest_download = downloads.latest('date')

            latest_opendata = region.opendata_set.last()

            if latest_opendata and latest_opendata.date == latest_download.date:
                continue

            data = [obj.as_dict() for obj in data_models.DTP.objects.filter(
                region__in=region.region_set.all(),
                datetime__date__lte=latest_download.date.replace(
                                day=calendar.monthrange(latest_download.date.year, latest_download.date.month)[1]
                            )
            )]

            geo_data = {"type": "FeatureCollection", "features": [
                {"type": "Feature",
                 "geometry": {"type": "Point", "coordinates": [item['point']['long'], item['point']['lat']]},
                 "properties": item
                 } for item in data
            ]}

            path = 'media/opendata/' + region.slug + '.geojson'
            with open(path, 'w') as data_file:
                json.dump(geo_data, data_file, ensure_ascii=False)

            latest_opendata, created = models.OpenData.objects.get_or_create(
                region=region
            )
            latest_opendata.date = latest_download.date
            latest_opendata.file_size = os.stat(path).st_size
            latest_opendata.save()
    """


def generate_datasets_geojson():
    data = [obj.as_dict() for obj in data_models.DTP.objects.all()]
    geo_data = { "type": "FeatureCollection", "features": [
        {"type": "Feature",
         "geometry": {"type": "Point", "coordinates": [item['point']['long'], item['point']['lat']]},
         "properties": item
         } for item in data
    ]}

    with open('static/data/' + 'test.geojson', 'w') as data_file:
        json.dump(geo_data, data_file, ensure_ascii=False)


def load_data():
    data = data_models.Region.objects.all()

    data = data.values('name', 'parent_region__name','gibdd_code', "ya_name", "slug")

    df = pd.DataFrame(data)
    df.to_csv('static/regions.csv', index=False)


def get_moderator_feedback(request):
    user = request.user
    if user.is_superuser:
        feedback = models.Feedback.objects.all()
    else:
        moderator = get_object_or_404(models.Moderator, user=request.user)
        feedback = models.Feedback.objects.filter(dtp__region__parent_region__moderator=moderator)

    return feedback


def is_moderator(user):
    try:
        get_object_or_404(models.Moderator, user=user)
        return True
    except:
        return False