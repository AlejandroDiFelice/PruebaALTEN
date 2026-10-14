import os
import requests
from google.cloud import bigquery

# Configurar la ruta de las credenciales de GCP (asegúrate de cambiar la ruta por la de tu JSON real)
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/ruta/a/tu/service-account.json"

class ApiClient:
    """Clase encargada de conectarse a la API y descargar los datos."""
    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_data(self, endpoint: str, limit: int = 100) -> list[dict]:
        """Se conecta a la API, obtiene los datos y los limita al número de registros deseado."""
        url = f"{self.base_url}/{endpoint}"
        print(f"Descargando datos desde: {url}...")
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Limitar a 100 registros como pide la prueba
            limited_data = data[:limit]
            print(f"¡Descarga exitosa! Se obtuvieron {len(limited_data)} registros.")
            return limited_data
        else:
            raise Exception(f"Error al conectar con la API: {response.status_code} - {response.text}")


class BigQueryLoader:
    """Clase encargada de gestionar la conexión y subida de datos a BigQuery."""
    def __init__(self, project_id: str, dataset_name: str, table_name: str):
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_name = dataset_name
        self.table_name = table_name
        self.table_id = f"{self.project_id}.{self.dataset_name}.{self.table_name}"

    def create_dataset_if_not_exists(self):
        """Crea el Dataset asegurando que siga la nomenclatura SANDBOX_<nombre_aplicacion>."""
        dataset_ref = bigquery.Dataset(f"{self.project_id}.{self.dataset_name}")
        dataset_ref.location = "US"  # Puedes cambiar la región según prefieras (ej. 'EU')
        try:
            dataset = self.client.create_dataset(dataset_ref, exists_ok=True)
            print(f"Dataset verificado/creado correctamente: {dataset.dataset_id}")
        except Exception as e:
            print(f"Error al crear el dataset: {e}")

    def upload_data(self, data: list[dict]):
        """Sube los datos en crudo (raw) a la tabla de BigQuery."""
        self.create_dataset_if_not_exists()
        
        # Configuración del trabajo de carga
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",  # O WRITE_TRUNCATE si prefieres sobrescribir en cada ejecución
        )

        print(f"Subiendo datos a la tabla BigQuery: {self.table_id}...")
        job = self.client.load_table_from_json(data, self.table_id, job_config=job_config)
        job.result()  # Esperar a que termine el proceso de carga

        # Verificar cuántas filas se cargaron
        table = self.client.get_table(self.table_id)
        print(f"¡Carga completada con éxito! La tabla tiene ahora {table.num_rows} filas.")


# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    # Parámetros de configuración
    PROJECT_ID = "tu-proyecto-gcp-id"  # <--- Reemplaza con tu Project ID de GCP
    APP_NAME = "miapp"                 # <--- Nombre de tu aplicación para la nomenclatura
    DATASET_NAME = f"SANDBOX_{APP_NAME}"
    TABLE_NAME = "raw_api_data"

    # 1. Descargar datos de la API
    api = ApiClient(base_url="https://jsonplaceholder.typicode.com")
    raw_data = api.fetch_data(endpoint="posts", limit=100)

    # 2. Subir datos a BigQuery
    bq_loader = BigQueryLoader(project_id=PROJECT_ID, dataset_name=DATASET_NAME, table_name=TABLE_NAME)
    bq_loader.upload_data(raw_data)