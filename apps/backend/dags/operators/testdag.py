from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
import pendulum
from src.api_client.M_api import get_weather_and_air_quality, insert_measurements_meto
from src.api_client.openweathermap_API import collect_measurements, insert_measurements_openweathermap

# Define default arguments
default_args = {
    'owner': 'airflow',
    'start_date': pendulum.today('UTC').add(days=-1),
    'retries': 1,
    'retry_delay': pendulum.duration(minutes=5),
}

# Define the DAG
dag = DAG(
    'weather_data_pipeline',
    default_args=default_args,
    description='Pipeline for collecting weather data from multiple sources',
    schedule='@daily',
    catchup=False,
    tags=['weather', 'api'],
)

# Create task groups for better organization
with dag:
    start_pipeline = EmptyOperator(
        task_id='start_pipeline'
    )

    # Meteo API Task Group
    with TaskGroup(group_id='meteo_operations') as meteo_group:
        meteo_collect = PythonOperator(
            task_id='collect_meteo_data',
            python_callable=get_weather_and_air_quality,
            do_xcom_push=True,  # Ensure the return value is pushed to XCom
            doc_md="""#### Task Documentation
            Collects weather data from Meteo API and pushes to XCom
            """,
        )

        meteo_load = PythonOperator(
            task_id='save_meteo_data',
            python_callable=insert_measurements_meto,
            provide_context=True,  # This allows accessing the context dictionary
            doc_md="""#### Task Documentation
            Pulls data from XCom and saves to database
            """,
        )

        meteo_collect >> meteo_load

    # OpenWeather API Task Group
    with TaskGroup(group_id='openweather_operations') as openweather_group:
        openweather_collect = PythonOperator(
            task_id='collect_openweather_data',
            python_callable=collect_measurements,
            do_xcom_push=True,
            doc_md="""#### Task Documentation
            Collects weather data from OpenWeatherMap API
            """,
        )
        openweather_load = PythonOperator(
            task_id='save_openweather_data',  # Changed from 'collect_openweather_data'
            python_callable=insert_measurements_openweathermap,
            provide_context=True,
            doc_md="""#### Task Documentation
            Saves weather data from OpenWeatherMap API to database
            """,  # Updated documentation to reflect the actual purpose
        )
        openweather_collect >> openweather_load

    end_pipeline = EmptyOperator(
        task_id='end_pipeline'
    )

    # Define the complete workflow
    start_pipeline >> meteo_group >> end_pipeline
    start_pipeline >>  openweather_group >> end_pipeline