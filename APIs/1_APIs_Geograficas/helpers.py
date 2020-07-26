import pandas as pd
import requests


def normalizar_unidades_territoriales(
        entidades, entidades_tipo, nombre_campo=None,
        provincia_campo=None, chunk_size=1000
):
    '''Normaliza unidades territoriales usando la API Georef.

    Args:
        entidades (list or pd.DataFrame): Una lista con nombres de entidades a
            normalizar, o un dataframe con columnas donde 'nombre_campo' es la
            que contiene los nombres a normalizar, y 'provincia_campo'
            (opcional) contiene el nombre del campo provincia, para mejorar el
            resultado de la normalizacion.
        entidades_tipo (str): Nombre del tipo de entidades a normalizar, puede
            ser uno de: 'provincias', 'departamentos', 'localidades' o
            'municipios'.
        nombre_campo (str): Debe especificarse si 'entidades' es un dataframe.
            Indica cual es el campo que contiene los nombres a normalizar.
        provincia_campo (str): Opcional. Indica cual es el campo que contiene
            los nombres de las provincias. Ayuda a mejorar la precision de la
            normalizacion de unidades mas chicas que provincias.

    Return:
        pd.DataFrame: Nombres y codigos oficiales de las entidades normalizadas.
    '''

    # genera un array vacio para guardar los resultados de cada request
    resultados = []

    # genera un resultado nulo para reemplazar los casos que no funcionen
    resultado_nulo = {
        'id': None,
        'nombre': None,
    }
    if provincia_campo:
        resultado_nulo['provincia_id'] = None
        resultado_nulo['provincia_nombre'] = None

    # genera el JSON con la lista de consultas a realizar
    for i in range(0, len(entidades), chunk_size):
        start, end = i, i + chunk_size

        # el final no puede ser mayor a la cantidad de entidades
        if end > len(entidades):
            end = len(entidades)

        data = {entidades_tipo: []}

        # si se pasa una lista, contiene los nombres a normalizar
        if isinstance(entidades, list):
            for nombre in entidades[start:end]:
                consulta = {
                    'nombre': nombre,
                    'max': 1,
                    'campos': 'id,nombre'
                }
                data[entidades_tipo].append(consulta)

        # si no se pasa una lista, debe haber un nombre de campo que contenga
        # los nombres a normalizar, y puede haber una columna de provincia
        elif nombre_campo:
            for entidad in entidades.to_dict('record')[start:end]:
                consulta = {
                    'nombre': entidad[nombre_campo],
                    'max': 1,
                    'campos': 'id,nombre',
                    'aplanar': True
                }
                if provincia_campo:
                    consulta['provincia'] = entidad[provincia_campo]
                    consulta['campos'] = 'id,nombre,provincia.id,provincia.nombre'

                data[entidades_tipo].append(consulta)
        else:
            print('Error en la definicion de la consulta')
            return

        try:
            # realiza la consulta
            resultados_parciales = requests.post(
                f"https://apis.datos.gob.ar/georef/api/{entidades_tipo}",
                json=data
            ).json()['resultados']

            for resultado in resultados_parciales:
                if resultado and resultado[entidades_tipo] and len(resultado[entidades_tipo]) != 0:
                    resultados.append(resultado[entidades_tipo][0])
                else:
                    resultados.append(resultado_nulo)

        except Exception as e:
            print(f'No se pudo normalizar el bloque {start} a {end}. '
                  'Reemplazando por resultados nulos.')
            print(e)
            resultados.extend([resultado_nulo] * (end - start))

    return pd.DataFrame(resultados)


def georreferenciar_direcciones(
        entidades, nombre_campo=None,
        provincia_campo=None, chunk_size=1000
):
    '''Normaliza unidades territoriales usando la API Georef.

    Args:
        entidades (pd.DataFrame): Una lista de direcciones a georreferenciar
            donde 'nombre_campo' es la que contiene las direcciones, y
            'provincia_campo' (opcional) contiene el nombre del campo provincia,
            para mejorar el resultado de la normalizacion.
        nombre_campo (str): Indica cual es el campo que contiene los nombres a
            normalizar.
        provincia_campo (str): Opcional. Indica cual es el campo que contiene
            los nombres de las provincias. Ayuda a mejorar la precision de la
            normalizacion de unidades mas chicas que provincias.

    Return:
        pd.DataFrame: Nombres y codigos oficiales de las entidades normalizadas.
    '''

    # genera un array vacio para guardar los resultados de cada request
    resultados = []

    # genera un resultado nulo para reemplazar los casos que no funcionen
    resultado_nulo = {
        'direccion_normalizada': None,
        'latitud': None,
        'longitud': None,
    }

    # genera el JSON con la lista de consultas a realizar
    for i in range(0, len(entidades), chunk_size):
        start, end = i, i + chunk_size

        # el final no puede ser mayor a la cantidad de entidades
        if end > len(entidades):
            end = len(entidades)

        data = {'direcciones': []}

        # si no se pasa una lista, debe haber un nombre de campo que contenga
        # los nombres a normalizar, y puede haber una columna de provincia
        for entidad in entidades.to_dict('record')[start:end]:
            consulta = {
                'direccion': entidad[nombre_campo],
                'max': 1,
                'campos': 'nomenclatura,ubicacion.lat,ubicacion.lon,provincia.id,provincia.nombre',
                'aplanar': True
            }
            if provincia_campo:
                consulta['provincia'] = entidad[provincia_campo]

            data['direcciones'].append(consulta)

        # try:
        # realiza la consulta
        resultados_parciales = requests.post(
            f"https://apis.datos.gob.ar/georef/api/direcciones",
            json=data
        ).json()['resultados']

        for resultado in resultados_parciales:
            if resultado and resultado['direcciones'] and len(resultado['direcciones']) != 0:
                resultado_parseado = {
                    'direccion_normalizada': resultado['direcciones'][0]['nomenclatura'],
                    'latitud': resultado['direcciones'][0]['ubicacion_lat'],
                    'longitud': resultado['direcciones'][0]['ubicacion_lon'],
                    'provincia_id': resultado['direcciones'][0]['provincia_id'],
                    'provincia_nombre': resultado['direcciones'][0]['provincia_nombre']
                }

                resultados.append(resultado_parseado)
            else:
                resultados.append(resultado_nulo)

        # except Exception as e:
        #     print(f'No se pudo normalizar el bloque {start} a {end}. '
        #           'Reemplazando por resultados nulos.')
        #     print(e)
        #     resultados.extend([resultado_nulo] * (end - start))

    return pd.DataFrame(resultados)
