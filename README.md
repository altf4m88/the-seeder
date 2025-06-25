# The Seeder

This project is a Python script designed to populate a PostgreSQL database with data from Excel files.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

* **Python 3:** This script is written in Python and requires a Python 3 environment.
* **PostgreSQL:** You need a running instance of PostgreSQL. The script will create the necessary tables, but the database itself must exist.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/altf4m88/the-seeder.git](https://github.com/altf4m88/the-seeder.git)
    cd the-seeder
    ```

2.  **Install dependencies:**

    This project requires several Python libraries. You can install them using `pip` and the provided `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Database Connection:**

    Open the `seed.py` file and locate the `DATABASE_URL` variable. You must change the placeholder with your actual PostgreSQL connection string.

    ```python
    # Replace with your actual PostgreSQL connection string.
    # Format: "postgresql://<user>:<password>@<host>:<port>/<dbname>"
    DATABASE_URL = "postgresql://awikwok:wikwokthetok@localhost/essaydb"
    ```

2.  **Clear Database on Start (Optional):**

    The `seed.py` script includes a `CLEAR_DATABASE_ON_START` flag.

    * If `CLEAR_DATABASE_ON_START` is set to `True`, the script will delete all data from the tables (`RequestLog`, `TaskAnswer`, `Question`, `Student`, `Subject`) before seeding new data.
    * If set to `False`, the script will add the new data without deleting existing records.

    ```python
    # IMPORTANT: This flag determines if the script clears the database before running.
    # Set to False if you want to add data without deleting existing records.
    CLEAR_DATABASE_ON_START = True
    ```

## Usage

1.  **Place your dataset:**

    Ensure your Excel files (`.xlsx`) are located in the `dataset` directory. The script will automatically find and process all `.xlsx` files in this folder.

2.  **Run the script:**

    Execute the `seed.py` script from your terminal:

    ```bash
    python seed.py
    ```

    The script will then connect to your database, create the tables if they don't exist, and populate them with the data from your Excel files.

## Database Schema

The script will create the following tables in your database:

* **subjects:** Stores subject names (e.g., "IPA", "Matematika").
* **students:** Stores student names.
* **questions:** Stores questions, their preferred answers, and links them to a subject.
* **task\_answers:** Stores student answers to questions, including a `ground_truth` boolean field.
* **request\_logs:** Logs requests made to the system, including token counts and request times.
