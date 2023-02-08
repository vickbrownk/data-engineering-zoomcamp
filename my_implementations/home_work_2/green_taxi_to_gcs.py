import pandas as pd
from pathlib import Path
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket


#First task is to fetch the data
@task(retries=3, retry_delay_seconds=5, log_prints=True)
def fetch_data(url:str) -> pd.DataFrame:
    df = pd.read_csv(url)
    print(f"rows: {len(df)}")
    return df

#next is to clean the data  that's stored in df
#save the data to our localfile and then upload to gcs
@task(log_prints=True)
def download_data_local(df:pd.DataFrame, color:str, dataset_file:str ) -> Path:
     #define a directory on the local you want to save the file
     data_dir = f'data/{color}'
     #use the path function to create and retrieve the directory you decided upon
     Path(data_dir).mkdir(parents=True, exist_ok=True)
     file_path = f'{data_dir}/{dataset_file}.csv'
     df.to_csv(file_path, index=False)
     return file_path

@task(log_prints=True)
def download_data_local_2(df:pd.DataFrame, color:str, dataset_file:str ) -> Path:
     #define a directory on the local you want to save the file
     data_dir = f"data/{color}"
     #use the path function to create and retrieve the directory you decided upon
     Path(data_dir).mkdir(parents=True, exist_ok=True)
     file_path_2 = f'{data_dir}/{dataset_file}.parquet'
     df.to_parquet(file_path_2, compression='gzip')
     return file_path_2

#after cleaning the data next we have to upload the data to gcs
@task(log_prints=True)
def upload_data(path:Path):
    gcs_block = GcsBucket.load("dezoomcamp")
    gcs_block.upload_from_path(from_path=path, to_path=path)
    return

@flow(log_prints=True)
def green_taxi_to_gcs(year: int, month: int, color: str)-> None:
    color = 'yellow'
    months = [2, 3]
    year = 2019
    dataset_file = f'{color}_tripdata_{year}-{month}'
    #url = f'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz'
    url_1 = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2019-02.csv.gz'
    url_2 = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2019-03.csv.gz'

    df_1 = fetch_data(url_1)
    df_2 = fetch_data(url_2)
    path = download_data_local(df_1, color, dataset_file)
    path_1 = download_data_local(df_2, color, dataset_file)
    path_2 = download_data_local_2(df_1, color, dataset_file)
    path_22 = download_data_local_2(df_2, color, dataset_file)
    upload_data(path)
    upload_data(path_1)
    upload_data(path_2)
    upload_data(path_22)

    
@flow(log_prints=True)
def upload_parent_flow(months: list[int] = [2, 3], year: int = 2019, color: str = 'yellow'):
    for month in months:
        green_taxi_to_gcs(year, month, color)

if __name__ == '__main__':
    color = 'yellow'
    months = [2, 3]
    year = 2019
    upload_parent_flow(months, year, color)
