# uvicorn funciones:app --reload
# http://localhost:8000/docs#/
# Cambios para forzar el redeploy

from fastapi import FastAPI, HTTPException
from typing import List, Dict

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a mi API con FastAPI!"}

import pandas as pd

# Cargar el dataset
dataset_movies = pd.read_csv("./dataset_final_movies.csv")
dataset_credits = pd.read_csv("./credits_dataset.csv")

print(dataset_movies.info())
print(dataset_credits.info())

dataset_movies["release_date"] = pd.to_datetime(dataset_movies["release_date"])

# Función para obtener la cantidad de filmaciones por mes
@app.get("/cantidad_filmaciones_mes/{mes}")
def cantidad_filmaciones_mes(mes: str):
    # Diccionario para convertir los nombres de los meses en español a números
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    
    # Validar el mes ingresado
    mes = mes.lower()
    if mes not in meses:
        return {"error": "Mes inválido. Por favor ingresa un mes en español."}
    
    # Obtener el número del mes
    mes_num = meses[mes]
    
    # Filtrar las películas por mes
    peliculas_mes = dataset_movies[dataset_movies["release_date"].dt.month == mes_num]
    cantidad = len(peliculas_mes)
    
    # Retornar la cantidad de películas
    return {
        "message": f"{cantidad} cantidad de películas fueron estrenadas en el mes de {mes.capitalize()}."
    }

# Diccionario para convertir los días de la semana en español a números (lunes = 0, domingo = 6)
dias = {
    "lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3, "viernes": 4, "sábado": 5, "domingo": 6
}

# Función para obtener la cantidad de filmaciones por día
@app.get("/cantidad_filmaciones_dia/{dia}")
def cantidad_filmaciones_dia(dia: str):
    # Validar el día ingresado
    dia = dia.lower()
    if dia not in dias:
        return {"error": "Día inválido. Por favor ingresa un día en español."}
    
    # Obtener el número del día
    dia_num = dias[dia]
    
    # Filtrar las películas por día de la semana
    peliculas_dia = dataset_movies[dataset_movies["release_date"].dt.weekday == dia_num]
    cantidad = len(peliculas_dia)
    
    # Retornar la cantidad de películas
    return {
        "message": f"{cantidad} cantidad de películas fueron estrenadas en el día {dia.capitalize()}."
    }
    
    # Definir un endpoint que recibe el título de una filmación
@app.get("/score_titulo/")
def score_titulo(titulo_de_la_filmacion: str):
    # Filtrar el DataFrame para encontrar la película con el título dado (ignorando mayúsculas y minúsculas)
    pelicula = dataset_movies[dataset_movies['title'].str.lower() == titulo_de_la_filmacion.lower()]

    # Si no se encuentra la película, lanzar una excepción HTTP 404
    if pelicula.empty:
        raise HTTPException(status_code=404, detail="Película no encontrada")

    # Extraer los datos necesarios de la primera coincidencia
    titulo = pelicula.iloc[0]['title']  # Título de la película
    anio = int(pelicula.iloc[0]['release_year'])  # Año de estreno
    score = float(pelicula.iloc[0]['vote_average'])  # Puntaje promedio de la película

    # Devolver la información como un diccionario (FastAPI lo convierte a JSON automáticamente)
    return {
        "titulo": titulo,
        "anio_estreno": anio,
        "score": score
    }
    
@app.get("/votes/{titulo_de_la_filmacion}")
def votos_titulo(titulo_de_la_filmacion: str):
    """
    Obtiene el título, la cantidad de votos y el promedio de votaciones de una filmación.
    Si la película tiene menos de 2000 votos, se devuelve un mensaje indicando que no cumple con la condición.
    """
    # Filtrar el dataset por título
    film = dataset_movies[dataset_movies["title"].str.lower() == titulo_de_la_filmacion.lower()]

    # Validar si la película existe
    if film.empty:
        raise HTTPException(status_code=404, detail="Película no encontrada.")

    # Extraer la cantidad de votos y el promedio
    votes = film.iloc[0]["vote_count"]
    average = film.iloc[0]["vote_average"]
    title = film.iloc[0]["title"]

    # Verificar si cumple con el umbral de 2000 votos
    if votes < 2000:
        return {"message": "La película no cumple con el mínimo de 2000 valoraciones."}

    # Respuesta exitosa
    return {
        "title": title,
        "vote_count": int(votes),
        "vote_average": float(average),
    }
    
    # Unir los datasets por la columna 'id', asegurando el mismo tipo de dato
dataset_credits['id'] = dataset_credits['id'].astype(str)
dataset_movies['id'] = dataset_movies['id'].astype(str)
    # Unir los datasets por la columna 'id'
data = pd.merge(dataset_credits, dataset_movies, on="id")


@app.get("/get_actor/{nombre_actor}")
def get_actor(nombre_actor: str):
    # Filtrar las filas donde el actor aparece en 'actor_names'
    actor_data = data[data['actor_names'].str.contains(nombre_actor, na=False, case=False)]

    if actor_data.empty:
        raise HTTPException(status_code=404, detail="Actor no encontrado")

    # Calcular métricas
    cantidad_peliculas = actor_data.shape[0]
    retorno_total = actor_data['return'].sum()
    promedio_retorno = retorno_total / cantidad_peliculas if cantidad_peliculas > 0 else 0

    # Crear respuesta
    respuesta = {
        "mensaje": f"El actor {nombre_actor} ha participado de {cantidad_peliculas} cantidad de filmaciones, el mismo ha conseguido un retorno de {retorno_total:.2f} con un promedio de {promedio_retorno:.2f} por filmación."
    }
    return respuesta

@app.get("/get_director/{nombre_director}")
def get_director(nombre_director: str):
    # Filtrar las películas dirigidas por el director
    director_movies = data[data["director_name"].str.contains(nombre_director, case=False, na=False)]

    if director_movies.empty:
        raise HTTPException(status_code=404, detail="Director not found")

    # Calcular el retorno total y construir la respuesta
    total_return = director_movies["return"].sum()
    movies_list = []

    for _, row in director_movies.iterrows():
        profit = row["revenue"] - row["budget"] if row["budget"] > 0 else 0

        movies_list.append({
            "title": row["title"],
            "release_date": row["release_date"],
            "individual_return": row["return"],
            "budget": row["budget"],
            "profit": profit
        })

    return {
        "director_name": nombre_director,
        "total_return": total_return,
        "movies": movies_list
    }