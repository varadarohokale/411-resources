from dataclasses import dataclass
import logging
import sqlite3
from typing import Any, List

from boxing.utils.sql_utils import get_db_connection
from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Boxer:
    """
    Represents a boxer with relevant attributes and automatically assigns a weight class.

    Attributes:
        id (int): THe unique number for the boxer.
        name (str): The name of the boxer.
        weight (int): The weight of the boxer in pounds.
        height (int): The height of the boxer in inches.
        reach (float): The arm reach of the boxer in inches.
        age (int): The age of the boxer in years.
        weight_class (str): The weight class of the boxer.

    Methods:
        __post_init__(): Automatically assigns a weight class to the boxer based on their weight.
    """
    id: int
    name: str
    weight: int
    height: int
    reach: float
    age: int
    weight_class: str = None

    def __post_init__(self):
        self.weight_class = get_weight_class(self.weight)  # Automatically assign weight class


def create_boxer(name: str, weight: int, height: int, reach: float, age: int) -> None:
    """
    Creates a new boxer and adds them to the database.

    Args:
        name (str): The name of the boxer.
        weight (int): The weight of the boxer in pounds (must be at least 125).
        height (int): The height of the boxer in inches (must be greater than 0).
        reach (float): The arm reach of the boxer in inches (must be greater than 0).
        age (int): The age of the boxer in years (must be between 18 and 40).

    Raises:
        ValueError: If any of the arguments are invalid.
    """
    logger.info("Attempting to create a new boxer.")

    if weight < 125:
        logger.error(f"Invalid weight: {weight}. Must be at least 125.")
        raise ValueError(f"Invalid weight: {weight}. Must be at least 125.")
    if height <= 0:
        logger.error(f"Invalid height: {height}. Must be greater than 0.")
        raise ValueError(f"Invalid height: {height}. Must be greater than 0.")
    if reach <= 0:
        logger.error(f"Invalid reach: {reach}. Must be greater than 0.")
        raise ValueError(f"Invalid reach: {reach}. Must be greater than 0.")
    if not (18 <= age <= 40):
        logger.error(f"Invalid age: {age}. Must be between 18 and 40.")
        raise ValueError(f"Invalid age: {age}. Must be between 18 and 40.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the boxer already exists (name must be unique)
            cursor.execute("SELECT 1 FROM boxers WHERE name = ?", (name,))
            if cursor.fetchone():
                logger.warning(f"Boxer with name '{name}' already exists")
                raise ValueError(f"Boxer with name '{name}' already exists")

            logger.info(f"Inserting new boxer")
            cursor.execute("""
                INSERT INTO boxers (name, weight, height, reach, age)
                VALUES (?, ?, ?, ?, ?)
            """, (name, weight, height, reach, age))

            conn.commit()
            logger.info(f"Sucessfully added new boxer: {name}")

    except sqlite3.IntegrityError:
        raise ValueError(f"Boxer with name '{name}' already exists")

    except sqlite3.Error as e:
        raise e


def delete_boxer(boxer_id: int) -> None:
    """
    Deletes a boxer from the database by their ID.

    Args:
        boxer_id (int): The unqiue number of the boxer.

    Raises:
        ValueError: If the boxer with the specified ID does not exist.
        sqlite3.Error: If a database error occurs during query execution.
    """

    logger.info("Attempting to delete a boxer")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            cursor.execute("DELETE FROM boxers WHERE id = ?", (boxer_id,))
            conn.commit()
            logger.info("Successfully deleted a boxer.")

    except sqlite3.Error as e:
        raise e


def get_leaderboard(sort_by: str = "wins") -> List[dict[str, Any]]:
    """
    Retrieves a leaderboard of boxers sorted by wins.

    Args:
        sort_by (str): The criteria to sort the leaderboard and must be either "wins" or "win_pct". 

    Returns:
        List[dict[str, Any]]: A list of dictionaries, where each dictionary contains 
            the details of a boxer.

    Raises:
        ValueError: If the `sort_by` parameter is not "wins" or "win_pct".
        sqlite3.Error: If a database error occurs
    """
    logger.info("Fetching leaderboard.")
    query = """
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.info(f"Invalid sort_by parameter: {sort_by}.")
        raise ValueError(f"Invalid sort_by parameter: {sort_by}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        leaderboard = []
        for row in rows:
            boxer = {
                'id': row[0],
                'name': row[1],
                'weight': row[2],
                'height': row[3],
                'reach': row[4],
                'age': row[5],
                'weight_class': get_weight_class(row[2]),  # Calculate weight class
                'fights': row[6],
                'wins': row[7],
                'win_pct': round(row[8] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(boxer)

        logger.info("Sucessfully fetched leaderboard.")
        return leaderboard

    except sqlite3.Error as e:
        raise e


def get_boxer_by_id(boxer_id: int) -> Boxer:
    """
    Retrieve the boxer by id

    Args: 
        boxer_id (int): The id number of a boxer.

    Returns:
        Boxer: A boxer if sucessful.

    Raises:
        ValueError: If the boxer's id is not found.
        sqlite3.Error: If a database error occurs
    """
    logger.info(f"Fetching boxer with ID {boxer_id}.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE id = ?
            """, (boxer_id,))

            row = cursor.fetchone()

            if row:
                logger.info(f"Boxer with ID {boxer_id} found.")
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                return boxer
            else:
                logger.error(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

    except sqlite3.Error as e:
        raise e


def get_boxer_by_name(boxer_name: str) -> Boxer:
    """
    Retrieve the boxer by name

    Args: 
        boxer_name (str): The name of a boxer.

    Returns:
        Boxer: A boxer if sucessful.

    Raises:
        ValueError: If the boxer's name is not found.

    """
    logger.info(f"Fetching boxer '{boxer_name}'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE name = ?
            """, (boxer_name,))

            row = cursor.fetchone()

            if row:
                logger.info(f"Boxer '{boxer_name}' found.")
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                return boxer
            else:
                logger.error(f"Boxer '{boxer_name}' not found.")
                raise ValueError(f"Boxer '{boxer_name}' not found.")

    except sqlite3.Error as e:
        raise e


def get_weight_class(weight: int) -> str:
    """
    Retrieve the weight class of a boxer

    Args: 
        weight (int): weight of a boxer

    Returns:
        (str) The name of the weight class of the specific boxer.

    Raises:
        ValueError: If the "weight" of the boxer is less than 125.

    """

    logger.info("Fetching weight class of a boxer.")

    if weight >= 203:
        weight_class = 'HEAVYWEIGHT'
    elif weight >= 166:
        weight_class = 'MIDDLEWEIGHT'
    elif weight >= 133:
        weight_class = 'LIGHTWEIGHT'
    elif weight >= 125:
        weight_class = 'FEATHERWEIGHT'
    else:
        logger.error(f"Invalid weight: {weight}. Weight must be at least 125.")
        raise ValueError(f"Invalid weight: {weight}. Weight must be at least 125.")

    logger.info("Sucessfully fetched weight class of a boxer.")
    return weight_class


def update_boxer_stats(boxer_id: int, result: str) -> None:
    """
    Update the statisitics of a boxer

    Args: 
        boxer_id (int): the number id specific to an individual boxer
        result (str): the win or loss a boxer gained 

    Returns:
        None

    Raises:
        ValueError: If the result is not a win or loss.

    """
    logger.info(f"Updating stats for boxer ID {boxer_id} with result '{result}'.")

    if result not in {'win', 'loss'}:
        logger.error(f"Invalid result: {result}. Expected 'win' or 'loss'.")
        raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.error(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            if result == 'win':
                cursor.execute("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?", (boxer_id,))
            else:  # result == 'loss'
                cursor.execute("UPDATE boxers SET fights = fights + 1 WHERE id = ?", (boxer_id,))

            conn.commit()
            logger.info(f"Stats updated successfully for boxer ID {boxer_id}.")


    except sqlite3.Error as e:
        raise e
